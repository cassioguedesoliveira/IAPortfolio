import unittest

from ragqa.chunking import chunk_text, load_directory
from ragqa.llm import ExtractiveLLM
from ragqa.pipeline import NO_ANSWER, RagPipeline
from ragqa.retriever import BM25Retriever, tokenize


class ChunkingTests(unittest.TestCase):
    def test_overlap_and_coverage(self):
        text = " ".join(str(i) for i in range(50))
        chunks = chunk_text(text, "doc.md", max_words=20, overlap=5)
        self.assertEqual(chunks[0].text.split()[-5:], chunks[1].text.split()[:5])
        self.assertIn("49", chunks[-1].text.split())

    def test_empty_text(self):
        self.assertEqual(chunk_text("   ", "x.md"), [])

    def test_invalid_params(self):
        with self.assertRaises(ValueError):
            chunk_text("a b c", "x", max_words=5, overlap=5)


class RetrieverTests(unittest.TestCase):
    def setUp(self):
        self.retriever = BM25Retriever()
        self.retriever.index(load_directory("data/docs"))

    def test_tokenize_strips_accents_and_stopwords(self):
        self.assertEqual(tokenize("A Política de Férias"), ["politica", "feria"])

    def test_ranks_relevant_document_first(self):
        top = self.retriever.search("meal reimbursement while travelling", top_k=1)[0]
        self.assertEqual(top.chunk.source, "expense_policy.md")

    def test_unrelated_query_returns_nothing(self):
        self.assertEqual(self.retriever.search("quantum chromodynamics lattice"), [])


class PipelineTests(unittest.TestCase):
    def setUp(self):
        retriever = BM25Retriever()
        retriever.index(load_directory("data/docs"))
        self.pipeline = RagPipeline(retriever, ExtractiveLLM())

    def test_answers_with_citation_and_sources(self):
        result = self.pipeline.answer("How many characters must a password have?")
        self.assertTrue(result.grounded)
        self.assertRegex(result.text, r"\[\d+\]")
        self.assertEqual(result.sources[0].source, "security_policy.md")

    def test_refuses_when_no_evidence(self):
        result = self.pipeline.answer("What is the capital of Mongolia?")
        self.assertEqual(result.text, NO_ANSWER)
        self.assertFalse(result.grounded)
        self.assertEqual(result.sources, [])

    def test_llm_not_called_without_evidence(self):
        class Boom:
            def generate(self, system, prompt):
                raise AssertionError("LLM must not be called")

        self.pipeline.llm = Boom()
        self.pipeline.answer("What is the capital of Mongolia?")

    def test_empty_question(self):
        with self.assertRaises(ValueError):
            self.pipeline.answer("  ")


if __name__ == "__main__":
    unittest.main()
