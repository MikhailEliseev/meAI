import pytest
@pytest.mark.asyncio
async def test_all():
    from meai.agents.operator import Operator
    assert Operator
