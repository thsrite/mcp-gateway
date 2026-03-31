from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import McpServerModel


async def create_server(session: AsyncSession, **kwargs) -> McpServerModel:
    server = McpServerModel(**kwargs)
    session.add(server)
    await session.commit()
    await session.refresh(server)
    return server


async def get_server(session: AsyncSession, server_id: int) -> McpServerModel | None:
    return await session.get(McpServerModel, server_id)


async def get_server_by_name(session: AsyncSession, name: str) -> McpServerModel | None:
    result = await session.execute(
        select(McpServerModel).where(McpServerModel.name == name)
    )
    return result.scalar_one_or_none()


async def list_servers(
    session: AsyncSession, status: str | None = None
) -> list[McpServerModel]:
    stmt = select(McpServerModel).order_by(McpServerModel.id)
    if status:
        stmt = stmt.where(McpServerModel.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_server(
    session: AsyncSession, server_id: int, **kwargs
) -> McpServerModel | None:
    server = await get_server(session, server_id)
    if not server:
        return None
    for key, value in kwargs.items():
        if hasattr(server, key):
            setattr(server, key, value)
    await session.commit()
    await session.refresh(server)
    return server


async def delete_server(session: AsyncSession, server_id: int) -> bool:
    server = await get_server(session, server_id)
    if not server:
        return False
    await session.delete(server)
    await session.commit()
    return True


async def list_enabled_servers(session: AsyncSession) -> list[McpServerModel]:
    result = await session.execute(
        select(McpServerModel).where(McpServerModel.enabled == True)
    )
    return list(result.scalars().all())


async def list_auto_update_servers(session: AsyncSession) -> list[McpServerModel]:
    result = await session.execute(
        select(McpServerModel).where(
            McpServerModel.auto_update == True,
            McpServerModel.enabled == True,
        )
    )
    return list(result.scalars().all())
