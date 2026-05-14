"""
Keyword-Research - Extracted skill implementation.

Source: Teacher Agent skill extraction
Adapted for AIM project structure
"""

import asyncio

params["max_results"] = max_results # type: ignore

    if client:
        response = await _rate_limit_request(client=client, url=BASE_URL, params=params)
        return _parse_arxiv_atom_response(response.text)
    else:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as new_client:
            response = await _rate_limit_request(client=new_client, url=BASE_URL, params=params)
            return _parse_arxiv_atom_response(response.text)
    
async def _rate_li