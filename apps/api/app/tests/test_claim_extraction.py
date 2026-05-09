import asyncio

from app.agents.claim_extraction_agent import ClaimExtractionAgent


def test_claim_extraction_classifies_housing_statement():
    output = asyncio.run(ClaimExtractionAgent().run(
        {
            "statements": [
                {
                    "statement_id": "s1",
                    "participant_id": "p1",
                    "cleaned_statement": "We need affordable housing more than another parking lot.",
                }
            ]
        }
    ))
    assert output["claims"]
    assert output["claims"][0]["value"] == "housing access"
    assert output["claims"][0]["claim_type"] == "proposal"
