from src import resume_parser, job_parser


def test_resume_parser_imports():
    # calling on empty input should not raise
    info = resume_parser.extract_info_from_text("")
    assert isinstance(info, dict)


def test_job_parser_empty():
    out = job_parser.parse_job_description("")
    assert out["title"] == "Not found"
