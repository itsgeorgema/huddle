import os

import pytest

from app.agents.claim_extraction_agent import ClaimExtractionAgent


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
async def test_claim_extraction_returns_structured_claims():
    output = await ClaimExtractionAgent().run(
        {
            "statements": [
                {
                    "statement_id": "s1",
                    "participant_id": "p1",
                    "cleaned_statement": "We need affordable housing more than another parking lot.",
                }
            ]
        }
    )
    assert output["claims"]
    claim = output["claims"][0]
    assert claim["participant_id"] == "p1"
    assert claim["statement_id"] == "s1"
    assert claim["text"]
    assert claim["claim_type"] in {"proposal", "impact", "priority", "concern", "factual"}
    assert claim["stakeholder"]
    assert claim["value"]
    assert 0.0 <= claim["confidence"] <= 1.0
