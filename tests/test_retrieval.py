import json
import tempfile
from pathlib import Path
import unittest
from dataset_intelligence.retrieval.bm25 import BM25Index
from dataset_intelligence.retrieval.dense import TestDenseEncoder, cosine
from dataset_intelligence.retrieval.documents import build_retrieval_document
from dataset_intelligence.retrieval.engine import RetrievalEngine
from dataset_intelligence.retrieval.fusion import reciprocal_rank_fusion
from dataset_intelligence.retrieval.metrics import evaluate
from dataset_intelligence.retrieval.query import RetrievalQuery, normalize_query

ROOT = Path(__file__).parents[1]


class QueryContractTests(unittest.TestCase):
    """Query normalization and structured constraint extraction."""

    def test_basic_modality_and_task(self):
        q = normalize_query("q", "Image classification for labels")
        self.assertEqual(q.modality, ("image",))
        self.assertIn("classification", q.task)

    def test_frozen_and_serializable(self):
        q = normalize_query("q", "tabular regression")
        d = q.to_dict()
        self.assertEqual(d["query_id"], "q")
        self.assertIn("regression", d["task"])
        self.assertIn("tabular", d["modality"])

    def test_empty_query(self):
        q = normalize_query("e", "")
        self.assertEqual(q.normalized_text, "")
        self.assertEqual(q.keywords, ())
        self.assertEqual(q.task, ())
        self.assertEqual(q.modality, ())

    def test_substring_does_not_false_match(self):
        """Term matching must be token-based, not substring-based."""
        # "textbook" should NOT match the "text" modality trigger
        q = normalize_query("q", "textbook classification")
        self.assertNotIn("text", q.modality)

        # "timetable" should NOT match the "tabular" trigger via "table"
        q2 = normalize_query("q", "timetable analysis")
        self.assertNotIn("tabular", q2.modality)

        # "recovery" should NOT match the "image" trigger via "cv"
        q3 = normalize_query("q", "recovery plan")
        self.assertNotIn("image", q3.modality)

    def test_legitimate_term_matches(self):
        """Actual tokens should still match correctly."""
        q = normalize_query("q", "cv image vision recognition")
        self.assertEqual(q.modality, ("image",))
        self.assertIn("classification", q.task)  # "recognition" triggers classification

        q2 = normalize_query("q", "csv tabular regression data")
        self.assertEqual(q2.modality, ("tabular",))
        self.assertIn("regression", q2.task)

    def test_multi_word_term_matching(self):
        """Multi-word terms like 'predict continuous' should match on tokens."""
        q = normalize_query("q", "predict continuous output values")
        self.assertIn("regression", q.task)

    def test_deterministic_across_calls(self):
        q1 = normalize_query("q", "image classification dataset")
        q2 = normalize_query("q", "image classification dataset")
        self.assertEqual(q1, q2)


class DocumentConstructionTests(unittest.TestCase):
    """Retrieval document construction from canonical records."""

    def test_excludes_popularity(self):
        record = json.loads(
            (ROOT / "experiments/m1/results/development_corpus.jsonl")
            .read_text().splitlines()[0]
        )
        doc = build_retrieval_document(record)
        self.assertNotIn("1200", doc["text"])
        self.assertIn("Movie", doc["text"])

    def test_preserves_dataset_id_and_source(self):
        record = json.loads(
            (ROOT / "experiments/m1/results/development_corpus.jsonl")
            .read_text().splitlines()[0]
        )
        doc = build_retrieval_document(record)
        self.assertTrue(doc["dataset_id"].startswith("ds_"))
        self.assertIsNotNone(doc["source"])
        self.assertIsInstance(doc["tokens"], tuple)
        self.assertTrue(len(doc["tokens"]) > 0)

    def test_all_corpus_documents_build(self):
        lines = (ROOT / "experiments/m1/results/development_corpus.jsonl").read_text().splitlines()
        ids = set()
        for line in lines:
            if not line.strip():
                continue
            doc = build_retrieval_document(json.loads(line))
            self.assertIn("dataset_id", doc)
            self.assertIn("text", doc)
            self.assertIn("tokens", doc)
            ids.add(doc["dataset_id"])
        self.assertEqual(len(ids), 10)


class BM25CorrectnessTests(unittest.TestCase):
    """BM25 ranking correctness on hand-checkable examples."""

    def _make_docs(self, texts):
        """Build minimal retrieval documents from plain text for BM25 testing."""
        import re
        docs = []
        for i, text in enumerate(texts):
            tokens = tuple(re.findall(r"[a-z0-9]+", text.lower()))
            docs.append({
                "dataset_id": f"ds_{i:04d}",
                "source": "test",
                "text": text,
                "tokens": tokens,
                "fields": {},
            })
        return docs

    def test_exact_term_ranked_higher(self):
        """A document containing the query term should rank above one that does not."""
        docs = self._make_docs([
            "iris flower classification",         # ds_0000: has "iris"
            "wine chemical analysis regression",  # ds_0001: no "iris"
            "iris setosa petal measurement",       # ds_0002: has "iris"
        ])
        idx = BM25Index(docs)
        results = idx.search(("iris",), 10)
        result_ids = [r[0]["dataset_id"] for r in results]
        self.assertEqual(len(results), 2)
        self.assertIn("ds_0000", result_ids)
        self.assertIn("ds_0002", result_ids)
        self.assertNotIn("ds_0001", result_ids)

    def test_multiple_term_overlap_scores_higher(self):
        """A document matching more query terms should score higher."""
        docs = self._make_docs([
            "image classification bean leaf disease",  # matches 3 terms
            "image classification dataset",            # matches 2 terms
            "tabular regression analysis",             # matches 0 query terms
        ])
        idx = BM25Index(docs)
        results = idx.search(("image", "classification", "bean"), 10)
        self.assertTrue(len(results) >= 2)
        # First result should be the one with 3 matching terms
        self.assertEqual(results[0][0]["dataset_id"], "ds_0000")
        self.assertEqual(results[1][0]["dataset_id"], "ds_0001")

    def test_empty_inputs(self):
        docs = self._make_docs(["iris flower"])
        idx = BM25Index(docs)
        self.assertEqual(idx.search((), 5), [])
        self.assertEqual(idx.search(("iris",), 0), [])

        empty_idx = BM25Index([])
        self.assertEqual(empty_idx.search(("iris",), 5), [])

    def test_deterministic_tie_breaking_by_dataset_id(self):
        """When BM25 scores are identical, results must be ordered by dataset_id."""
        # Two documents with identical content => identical scores
        docs = self._make_docs([
            "identical content classification",
            "identical content classification",
        ])
        # Manually set distinct IDs to test ordering
        docs[0]["dataset_id"] = "ds_beta"
        docs[1]["dataset_id"] = "ds_alpha"
        idx = BM25Index(docs)
        results = idx.search(("identical", "classification"), 10)
        self.assertEqual(len(results), 2)
        # Same scores => sorted ascending by dataset_id
        self.assertEqual(results[0][0]["dataset_id"], "ds_alpha")
        self.assertEqual(results[1][0]["dataset_id"], "ds_beta")
        # Scores must actually be equal
        self.assertAlmostEqual(results[0][1], results[1][1], places=10)


class DenseIndexTests(unittest.TestCase):
    """Dense retrieval determinism and correctness."""

    def test_cosine_identical_vectors(self):
        self.assertAlmostEqual(cosine([1, 0, 0], [1, 0, 0]), 1.0)

    def test_cosine_orthogonal_vectors(self):
        self.assertAlmostEqual(cosine([1, 0], [0, 1]), 0.0)

    def test_cosine_zero_vector(self):
        self.assertAlmostEqual(cosine([0, 0], [1, 1]), 0.0)

    def test_dense_deterministic_ordering(self):
        """Dense retrieval with TestDenseEncoder must be deterministic."""
        encoder = TestDenseEncoder()
        config = {"bm25": {"k1": 1.2, "b": 0.75}, "hybrid": {"rrf_k": 60}}
        engine = RetrievalEngine.from_jsonl(
            ROOT / "experiments/m1/results/development_corpus.jsonl",
            encoder, config,
        )
        q = normalize_query("q", "image classification bean")
        r1 = engine.retrieve(q, 5, "dense")
        r2 = engine.retrieve(q, 5, "dense")
        self.assertEqual(
            [x["dataset_id"] for x in r1],
            [x["dataset_id"] for x in r2],
        )


class RRFTests(unittest.TestCase):
    """Reciprocal rank fusion behavior."""

    def test_deduplicates_across_methods(self):
        rows = reciprocal_rank_fusion(
            {"a": [{"dataset_id": "x", "source": "s", "score": 1}],
             "b": [{"dataset_id": "x", "source": "s", "score": 1}]}, 5
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0]["contributions"]), {"a", "b"})

    def test_rrf_ranks_are_contiguous(self):
        rows = reciprocal_rank_fusion({
            "a": [{"dataset_id": "x", "source": "s", "score": 2},
                  {"dataset_id": "y", "source": "s", "score": 1}],
            "b": [{"dataset_id": "y", "source": "s", "score": 2},
                  {"dataset_id": "z", "source": "s", "score": 1}],
        }, 10)
        ranks = [r["rank"] for r in rows]
        self.assertEqual(ranks, list(range(1, len(rows) + 1)))

    def test_rrf_method_field(self):
        rows = reciprocal_rank_fusion(
            {"m1": [{"dataset_id": "a", "source": "s", "score": 1}]}, 5
        )
        self.assertEqual(rows[0]["method"], "hybrid_rrf")


class RetrievalEngineTests(unittest.TestCase):
    """Full engine integration tests."""

    def setUp(self):
        config = {"bm25": {"k1": 1.2, "b": 0.75}, "hybrid": {"rrf_k": 60}}
        self.engine = RetrievalEngine.from_jsonl(
            ROOT / "experiments/m1/results/development_corpus.jsonl",
            TestDenseEncoder(), config,
        )

    def test_all_modes_and_schema(self):
        q = normalize_query("q", "bean leaf image classification")
        for rows in (
            self.engine.retrieve(q, 5, "bm25"),
            self.engine.retrieve(q, 5, "dense"),
            self.engine.retrieve_hybrid(q, 5),
        ):
            self.assertTrue(rows)
            for x in rows:
                self.assertIn("dataset_id", x)
                self.assertIn("method", x)
                self.assertIn("rank", x)
                self.assertIn("score", x)
                self.assertIn("query_id", x)
                self.assertIn("index_version", x)
                self.assertTrue(x["dataset_id"].startswith("ds_"))

    def test_empty_query_returns_empty(self):
        self.assertEqual(
            self.engine.retrieve(normalize_query("e", ""), 5, "bm25"), []
        )

    def test_empty_corpus_returns_empty(self):
        empty = RetrievalEngine([], TestDenseEncoder(), {"bm25": {}, "hybrid": {}})
        self.assertEqual(
            empty.retrieve(normalize_query("q", "iris"), 5, "bm25"), []
        )

    def test_invalid_method_raises(self):
        q = normalize_query("q", "iris")
        with self.assertRaises(ValueError):
            self.engine.retrieve(q, 5, "invalid")

    def test_hybrid_results_have_query_id_and_version(self):
        q = normalize_query("q", "wine classification")
        rows = self.engine.retrieve_hybrid(q, 5)
        for r in rows:
            self.assertEqual(r["query_id"], "q")
            self.assertEqual(r["index_version"], "hybrid-rrf-v1")


class MetadataAndReproducibilityTests(unittest.TestCase):
    """Metadata propagation and corpus reproducibility."""

    def test_save_metadata_records_versions(self):
        config = {"bm25": {"k1": 1.2, "b": 0.75}, "hybrid": {"rrf_k": 60}}
        engine = RetrievalEngine.from_jsonl(
            ROOT / "experiments/m1/results/development_corpus.jsonl",
            TestDenseEncoder(), config,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata = engine.save_metadata(tmpdir)
            self.assertEqual(metadata["index_schema_version"], "1")
            self.assertEqual(metadata["bm25_version"], "bm25-v1")
            self.assertEqual(metadata["dense_version"], "dense-v1")
            self.assertEqual(metadata["embedding_model"], "test-token-vector-v1")
            self.assertEqual(metadata["corpus_records"], 10)
            self.assertIn("corpus_hash", metadata)
            self.assertIn("python_version", metadata)
            self.assertIn("platform", metadata)
            self.assertEqual(metadata["config"], config)
            # Verify file was written
            written = json.loads((Path(tmpdir) / "metadata.json").read_text())
            self.assertEqual(written["corpus_hash"], metadata["corpus_hash"])

    def test_corpus_hash_is_deterministic(self):
        """Same input records and config must produce the same corpus hash."""
        config = {"bm25": {"k1": 1.2, "b": 0.75}, "hybrid": {"rrf_k": 60}}
        e1 = RetrievalEngine.from_jsonl(
            ROOT / "experiments/m1/results/development_corpus.jsonl",
            TestDenseEncoder(), config,
        )
        e2 = RetrievalEngine.from_jsonl(
            ROOT / "experiments/m1/results/development_corpus.jsonl",
            TestDenseEncoder(), config,
        )
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            m1 = e1.save_metadata(d1)
            m2 = e2.save_metadata(d2)
            self.assertEqual(m1["corpus_hash"], m2["corpus_hash"])
            self.assertEqual(m1["corpus_records"], m2["corpus_records"])


class MetricsCorrectnessTests(unittest.TestCase):
    """IR metric computation correctness."""

    def test_perfect_recall(self):
        m = evaluate([{"dataset_id": "x"}], {"x": 2})
        self.assertEqual(m["recall@1"], 1.0)
        self.assertEqual(m["precision@1"], 1.0)
        self.assertEqual(m["mrr@1"], 1.0)

    def test_zero_recall(self):
        m = evaluate([{"dataset_id": "y"}], {"x": 1})
        self.assertEqual(m["recall@1"], 0.0)
        self.assertEqual(m["precision@1"], 0.0)
        self.assertEqual(m["mrr@1"], 0.0)

    def test_ndcg_perfect_at_1(self):
        m = evaluate([{"dataset_id": "x"}], {"x": 3})
        self.assertAlmostEqual(m["ndcg@1"], 1.0)

    def test_recall_grows_with_k(self):
        results = [{"dataset_id": "a"}, {"dataset_id": "b"}, {"dataset_id": "c"}]
        m = evaluate(results, {"b": 1, "c": 1})
        self.assertLessEqual(m["recall@1"], m["recall@3"])

    def test_empty_relevance(self):
        m = evaluate([{"dataset_id": "x"}], {})
        self.assertEqual(m["recall@1"], 0.0)
        self.assertEqual(m["precision@1"], 0.0)


if __name__ == "__main__":
    unittest.main()
