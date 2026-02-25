from wandavoice.improve import improve_text


def test_improve_basic_removes_fillers():
    out = improve_text("äh also das ist quasi ein test", "basic")
    assert out == "das ist ein test"


def test_improve_prompt_llm_adds_sentence_end():
    out = improve_text("kannst du das besser strukturieren", "prompt", target="cli:gemini")
    assert "SYSTEM TASK" in out
    assert "INPUT (question)" in out
    assert "kannst du das besser strukturieren?" in out.lower()


def test_improve_prompt_non_llm_stays_conservative():
    out = improve_text("kannst du das besser strukturieren", "prompt", target="insert")
    assert out == "kannst du das besser strukturieren"
