import pytest
from unittest.mock import patch, MagicMock
from cortex.engine.cortex_llm_adapters import (
    invocar_cortex_llm_sota,
    GeminiAdapter,
    ClaudeOpusAdapter,
    O4OmegaAdapter
)

# Mocked responses for the C5-REAL engine
VALID_JSON_RESPONSE = '''
{
  "Claim": "Reentrancy extracted in withdraw()",
  "Proof": {"Base": "0x123", "Confidence": "C5"},
  "Deltas": [{"op": "replace", "path": "test", "content": "test"}]
}
'''

INVALID_PROSE_RESPONSE = '''
Here is the analysis of the contract:
{
  "Claim": "Reentrancy extracted",
  "Proof": {"Base": "0x123", "Confidence": "C4"},
  "Deltas": []
}
As you can see, there is a vulnerability here.
'''

@patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'})
@patch('cortex.engine.cortex_llm_adapters.httpx.Client')
def test_gemini_sota_success(mock_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": VALID_JSON_RESPONSE}]}}]
    }
    mock_client.return_value.__enter__.return_value.post.return_value = mock_response
    
    delta = invocar_cortex_llm_sota("prompt", target_model="gemini-3.1-pro")
    
    assert delta.claim == "Reentrancy extracted in withdraw()"
    assert delta.confidence == "C5"
    assert delta.raw_exergy >= 0.8

@patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'})
@patch('cortex.engine.cortex_llm_adapters.Anthropic')
def test_claude_sota_success(mock_anthropic):
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=VALID_JSON_RESPONSE)]
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client
    
    delta = invocar_cortex_llm_sota("prompt", target_model="claude-4.6-opus")
    
    assert delta.claim == "Reentrancy extracted in withdraw()"
    
@patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
@patch('cortex.engine.cortex_llm_adapters.OpenAI')
def test_o4_sota_success(mock_openai):
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.message.content = VALID_JSON_RESPONSE
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_message])
    mock_openai.return_value = mock_client
    
    delta = invocar_cortex_llm_sota("prompt", target_model="o4-omega")
    
    assert delta.claim == "Reentrancy extracted in withdraw()"

@patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
@patch('cortex.engine.cortex_llm_adapters.OpenAI')
def test_o4_thermal_bleed_failure(mock_openai):
    # Simulate a model that refuses to stop generating prose (Green Theater)
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.message.content = INVALID_PROSE_RESPONSE
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_message])
    mock_openai.return_value = mock_client
    
    # Engine defaults to 3 retries, so if it always returns prose, it will eventually raise RuntimeError
    with pytest.raises(RuntimeError, match="CORTEX-LLM: Thermal Bleed Exceeded"):
        invocar_cortex_llm_sota("prompt", target_model="o4-omega")
