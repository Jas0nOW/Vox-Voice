from wandavoice.llm import GeminiLLM

def test_parse_response_say_show():
    llm = GeminiLLM.__new__(GeminiLLM)
    say, show = llm.parse_response("SAY: hi\nSHOW: details")
    assert say == "hi"
    assert show == "details"

def test_parse_response_fallback():
    llm = GeminiLLM.__new__(GeminiLLM)
    say, show = llm.parse_response("One. Two. Three. Four. Five.")
    assert "One." in say
    assert show != ""
