import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import (
    create_server,
    delete_server,
    get_server,
    get_server_by_name,
    list_servers,
    update_server,
)
from app.db.engine import get_session
from app.schemas.common import ApiResponse
from app.schemas.mcp_server import ServerCreate, ServerResponse, ServerUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_modules():
    from app.main import aggregator, client_pool, github_manager, log_collector
    return github_manager, client_pool, aggregator, log_collector


@router.get("", response_model=ApiResponse)
async def api_list_servers(
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    _, _, aggregator, _ = _get_modules()
    servers = await list_servers(session, status=status)
    result = []
    for s in servers:
        data = s.to_dict()
        data["tools_count"] = aggregator.get_tools_count(s.id) if aggregator else 0
        result.append(data)
    return ApiResponse(data=result)


@router.post("", response_model=ApiResponse)
async def api_create_server(
    body: ServerCreate,
    session: AsyncSession = Depends(get_session),
):
    github_manager, client_pool, aggregator, _ = _get_modules()

    if body.github_url:
        # Clone from GitHub
        try:
            clone_result = await github_manager.clone(body.github_url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Clone failed: {e}")

        name = body.name or clone_result.detected_name
        if await get_server_by_name(session, name):
            raise HTTPException(status_code=400, detail=f"Server name '{name}' already exists")

        server = await create_server(
            session,
            name=name,
            github_url=body.github_url,
            local_path=str(clone_result.local_path),
            project_type=clone_result.project_type,
            command=body.command or clone_result.command,
            args=body.args or clone_result.args,
            env=body.env or {},
            auto_update=body.auto_update,
            auto_restart=body.auto_restart,
            last_commit=clone_result.commit_hash,
        )
    else:
        # Manual configuration
        if not body.name or not body.command or not body.local_path:
            raise HTTPException(
                status_code=400,
                detail="name, command, and local_path are required for manual configuration",
            )

        if await get_server_by_name(session, body.name):
            raise HTTPException(status_code=400, detail=f"Server name '{body.name}' already exists")

        server = await create_server(
            session,
            name=body.name,
            local_path=body.local_path,
            command=body.command,
            args=body.args or [],
            env=body.env or {},
            auto_update=body.auto_update,
            auto_restart=body.auto_restart,
        )

    # Start the server
    try:
        await client_pool.add(
            server_id=server.id,
            namespace=server.name,
            command=server.command,
            args=server.args or [],
            cwd=server.local_path,
            env=server.env,
        )
        await aggregator.refresh_one(server.id)
        await update_server(session, server.id, status="running")
        server.status = "running"
    except Exception as e:
        await update_server(session, server.id, status="error")
        server.status = "error"
        logger.error(f"Failed to start server {server.name}: {e}")

    data = server.to_dict()
    data["tools_count"] = aggregator.get_tools_count(server.id)
    return ApiResponse(data=data)


@router.get("/{server_id}", response_model=ApiResponse)
async def api_get_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
):
    _, _, aggregator, _ = _get_modules()
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    data = server.to_dict()
    data["tools_count"] = aggregator.get_tools_count(server.id)
    return ApiResponse(data=data)


@router.put("/{server_id}", response_model=ApiResponse)
async def api_update_server(
    server_id: int,
    body: ServerUpdate,
    session: AsyncSession = Depends(get_session),
):
    _, client_pool, aggregator, _ = _get_modules()
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    server = await update_server(session, server_id, **update_data)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # If command/args/env changed and server is running, restart it
    restart_fields = {"command", "args", "env", "name"}
    if restart_fields & set(update_data.keys()) and server.status == "running":
        try:
            await client_pool.remove(server_id)
            await client_pool.add(
                server_id=server.id,
                namespace=server.name,
                command=server.command,
                args=server.args or [],
                cwd=server.local_path,
                env=server.env,
            )
            await aggregator.refresh_one(server.id)
        except Exception as e:
            await update_server(session, server_id, status="error")
            logger.error(f"Failed to restart server after update: {e}")

    data = server.to_dict()
    data["tools_count"] = aggregator.get_tools_count(server.id)
    return ApiResponse(data=data)


@router.delete("/{server_id}", response_model=ApiResponse)
async def api_delete_server(
    server_id: int,
    delete_repo: bool = False,
    session: AsyncSession = Depends(get_session),
):
    github_manager, client_pool, aggregator, log_collector = _get_modules()
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Stop and remove from pool
    await client_pool.remove(server_id)
    aggregator.remove_server(server_id)
    if log_collector:
        log_collector.stop_collecting(server_id)

    # Delete repo if requested
    if delete_repo and server.local_path:
        await github_manager.delete_repo(Path(server.local_path))

    await delete_server(session, server_id)
    return ApiResponse(message=f"Server '{server.name}' deleted")


@router.post("/{server_id}/start", response_model=ApiResponse)
async def api_start_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
):
    _, client_pool, aggregator, _ = _get_modules()
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if server.status == "running":
        return ApiResponse(message="Server is already running")

    try:
        await client_pool.add(
            server_id=server.id,
            namespace=server.name,
            command=server.command,
            args=server.args or [],
            cwd=server.local_path,
            env=server.env,
        )
        await aggregator.refresh_one(server.id)
        await update_server(session, server_id, status="running", enabled=True)
        return ApiResponse(message=f"Server '{server.name}' started")
    except Exception as e:
        await update_server(session, server_id, status="error")
        raise HTTPException(status_code=500, detail=f"Failed to start: {e}")


@router.post("/{server_id}/stop", response_model=ApiResponse)
async def api_stop_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
):
    _, client_pool, aggregator, _ = _get_modules()
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    await client_pool.remove(server_id)
    aggregator.remove_server(server_id)
    await update_server(session, server_id, status="stopped", enabled=False)
    return ApiResponse(message=f"Server '{server.name}' stopped")


@router.post("/{server_id}/restart", response_model=ApiResponse)
async def api_restart_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
):
    _, client_pool, aggregator, _ = _get_modules()
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    try:
        await client_pool.remove(server_id)
        await client_pool.add(
            server_id=server.id,
            namespace=server.name,
            command=server.command,
            args=server.args or [],
            cwd=server.local_path,
            env=server.env,
        )
        await aggregator.refresh_one(server.id)
        await update_server(session, server_id, status="running")
        return ApiResponse(message=f"Server '{server.name}' restarted")
    except Exception as e:
        await update_server(session, server_id, status="error")
        raise HTTPException(status_code=500, detail=f"Failed to restart: {e}")


@router.post("/{server_id}/update", response_model=ApiResponse)
async def api_update_repo(
    server_id: int,
    session: AsyncSession = Depends(get_session),
):
    github_manager, client_pool, aggregator, _ = _get_modules()
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not server.github_url:
        raise HTTPException(status_code=400, detail="Server has no GitHub URL")

    try:
        result = await github_manager.pull(Path(server.local_path))
        if result.has_updates:
            await update_server(session, server_id, last_commit=result.commit_after)
            # Restart if running
            if server.status == "running":
                await client_pool.remove(server_id)
                await client_pool.add(
                    server_id=server.id,
                    namespace=server.name,
                    command=server.command,
                    args=server.args or [],
                    cwd=server.local_path,
                    env=server.env,
                )
                await aggregator.refresh_one(server.id)
            return ApiResponse(
                message=f"Updated: {result.commit_before[:8]} -> {result.commit_after[:8]}"
            )
        return ApiResponse(message="Already up to date")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {e}")


@router.get("/{server_id}/tools", response_model=ApiResponse)
async def api_get_server_tools(
    server_id: int,
    session: AsyncSession = Depends(get_session),
):
    _, _, aggregator, _ = _get_modules()
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    tools = aggregator.list_server_tools(server_id)
    return ApiResponse(data=tools)


@router.get("/{server_id}/resources", response_model=ApiResponse)
async def api_get_server_resources(
    server_id: int,
    session: AsyncSession = Depends(get_session),
):
    _, _, aggregator, _ = _get_modules()
    server = await get_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    resources = aggregator.list_server_resources(server_id)
    return ApiResponse(data=resources)
