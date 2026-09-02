"""Adapter boundary: source payload -> canonical record, with no ranking logic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from .normalization import MODALITY_MAP, TASK_MAP, normalize_count, normalize_text, normalize_timestamp, normalize_url, normalized_terms, stable_internal_id
from .schema import SCHEMA_VERSION, CanonicalDataset, SourceClaim


class SourceAdapter(ABC):
    source_name: str

    @abstractmethod
    def discover(self, query: str) -> str | None: ...

    @abstractmethod
    def fetch_metadata(self, source_dataset_id: str) -> str: ...

    @abstractmethod
    def normalize(self, raw: dict[str, Any], observed_at: str) -> CanonicalDataset: ...

    def identify(self, raw: dict[str, Any]) -> tuple[str, str | None]:
        identifier = str(raw.get("id") or raw.get("did") or raw.get("ref") or raw["source_dataset_id"])
        return identifier, str(raw.get("version") or raw.get("sha") or "") or None

    @abstractmethod
    def capability_report(self) -> dict[str, Any]: ...

    @abstractmethod
    def access_policy(self) -> dict[str, Any]: ...

    def _record(self, *, raw: dict[str, Any], observed_at: str, dataset_id: str, version_id: str | None, name: object, url: object, description: object, tasks: object = None, modalities: object = None, tags: object = None, sample_count: object = None, class_count: object = None, license_claim: object = None, creators: object = None, citation: object = None, documentation_url: object = None, downloads: object = None, stars: object = None, formats: object = None, splits: object = None, feature_info: object = None, family_id: object = None, lineage: object = None, croissant_url: object = None, raw_reference: str = "fixture") -> CanonicalDataset:
        canonical_url = normalize_url(str(url)) or ""
        task, unresolved_task = normalized_terms(tasks, TASK_MAP)
        modality, unresolved_modality = normalized_terms(modalities, MODALITY_MAP)
        normalized_tags = sorted({term for term in (normalize_text(item) for item in (tags or [])) if term})
        claim_values = {"dataset_name": name, "description": description, "task": tasks, "modality": modalities, "sample_count": sample_count, "class_count": class_count, "license_claim": license_claim, "version_id": version_id, "dataset_family_id": family_id}
        claims = {key: [SourceClaim(value=value, source_url=canonical_url, source_field=key, observed_at=observed_at)] for key, value in claim_values.items() if value is not None}
        missing = [key for key, value in claim_values.items() if value is None]
        record = CanonicalDataset(
            schema_version=SCHEMA_VERSION, adapter_version=self.adapter_version, internal_id=stable_internal_id(self.source_name, dataset_id, version_id),
            identity={"source_name": self.source_name, "source_dataset_id": dataset_id, "dataset_name": normalize_text(name), "canonical_url": canonical_url, "version_id": version_id, "dataset_family_id": normalize_text(family_id), "lineage": lineage or {"state": "unresolved"}},
            semantics={"description": normalize_text(description), "task": task or None, "domain": None, "modality": modality or None, "learning_type": None, "target": None, "label_type": None, "tags": normalized_tags, "intended_use": None},
            structure={"sample_count": normalize_count(sample_count), "class_count": normalize_count(class_count), "schema_summary": None, "formats": formats or [], "splits": splits or [], "feature_information": feature_info or None},
            governance={"license_claim": normalize_text(license_claim), "usage_policy": None, "creators": creators or [], "citation": normalize_text(citation), "documentation_url": normalize_url(str(documentation_url)) if documentation_url else canonical_url, "provenance_urls": [canonical_url] if canonical_url else [], "croissant_url": normalize_url(str(croissant_url)) if croissant_url else None},
            community_context={"downloads": normalize_count(downloads), "stars": normalize_count(stars), "ratings": None, "citations": None, "updated_at": normalize_timestamp(raw.get("lastModified") or raw.get("updated_at")), "repository_activity": None},
            access={"access_type": self.capability_report()["access_type"], "metadata_accessible": True, "sample_accessible": self.capability_report()["sample_accessible"], "sampling_method": self.capability_report()["sampling_method"], "estimated_access_cost": "unknown", "source_policy_status": self.access_policy()["status"], "cache_status": "fixture", "observed_at": observed_at, "source_response_identifiers": {"raw_reference": raw_reference}},
            observed_content={"sample_count_observed": None, "content_fingerprint": None, "duplicate_rate": None, "outlier_rate": None, "label_issue_rate": None, "probe_metrics": None, "utility_estimate": None},
            risk_uncertainty={"risk_flags": [], "missing_fields": missing, "unresolved_claims": sorted(set(unresolved_task + unresolved_modality)), "access_limitations": self.capability_report()["limitations"]}, claims=claims,
            provenance=[{"source_url": canonical_url, "observed_at": observed_at, "adapter_version": self.adapter_version, "raw_reference": raw_reference, "raw_retained": True}],
        )
        record.validate()
        return record


class HuggingFaceAdapter(SourceAdapter):
    source_name, adapter_version = "huggingface", "1.0"
    def discover(self, query: str) -> str | None: return f"https://huggingface.co/api/datasets?search={query}&limit=20"
    def fetch_metadata(self, source_dataset_id: str) -> str: return f"https://huggingface.co/api/datasets/{source_dataset_id}"
    def capability_report(self) -> dict[str, Any]: return {"metadata_discovery": True, "metadata_retrieval": True, "sample_retrieval": True, "viewer_access": True, "streaming": False, "authentication_required": False, "programmatic_access": "allowed_public", "rate_limits": "unknown", "bounded_sampling": True, "access_type": "public_api_and_viewer", "sample_accessible": "conditional", "sampling_method": "documented_dataset_viewer_rows", "limitations": ["viewer availability can fail; M0 observed HTTP 502"]}
    def access_policy(self) -> dict[str, Any]: return {"status": "documented_public_viewer", "url": "https://huggingface.co/docs/dataset-viewer/rows"}
    def normalize(self, raw: dict[str, Any], observed_at: str) -> CanonicalDataset:
        card = raw.get("cardData") or {}
        dataset_id, version = self.identify(raw)
        tasks = card.get("task_categories") or raw.get("tags")
        modalities = card.get("modalities") or raw.get("tags")
        return self._record(raw=raw, observed_at=observed_at, dataset_id=dataset_id, version_id=version, name=raw.get("id"), url=f"https://huggingface.co/datasets/{dataset_id}", description=raw.get("description"), tasks=tasks, modalities=modalities, tags=raw.get("tags") or [], sample_count=card.get("size_categories"), license_claim=card.get("license"), creators=[raw["author"]] if raw.get("author") else [], documentation_url=f"https://huggingface.co/datasets/{dataset_id}", downloads=raw.get("downloads"), stars=raw.get("likes"), formats=[item.get("rfilename") for item in raw.get("siblings", []) if item.get("rfilename")], croissant_url=raw.get("croissant_url"), raw_reference="huggingface_fixture")


class OpenMLAdapter(SourceAdapter):
    source_name, adapter_version = "openml", "1.0"
    def discover(self, query: str) -> str | None: return "https://www.openml.org/api/v1/json/data/list/limit/20"
    def fetch_metadata(self, source_dataset_id: str) -> str: return f"https://www.openml.org/api/v1/json/data/{source_dataset_id}"
    def capability_report(self) -> dict[str, Any]: return {"metadata_discovery": True, "metadata_retrieval": True, "sample_retrieval": True, "viewer_access": False, "streaming": False, "authentication_required": False, "programmatic_access": "allowed_public", "rate_limits": "unknown", "bounded_sampling": True, "access_type": "public_rest", "sample_accessible": "conditional", "sampling_method": "metadata_link_bounded_stream", "limitations": []}
    def access_policy(self) -> dict[str, Any]: return {"status": "documented_public_rest", "url": "https://docs.openml.org/ecosystem/Rest/"}
    def normalize(self, raw: dict[str, Any], observed_at: str) -> CanonicalDataset:
        data = raw.get("data_set_description", raw); dataset_id, version = self.identify(data)
        return self._record(raw=data, observed_at=observed_at, dataset_id=dataset_id, version_id=version, name=data.get("name"), url=f"https://www.openml.org/d/{dataset_id}", description=data.get("description"), tasks=data.get("tag"), modalities=[data.get("format")] if data.get("format") else [], tags=data.get("tag") or [], sample_count=data.get("NumberOfInstances"), class_count=data.get("NumberOfClasses"), license_claim=data.get("licence"), creators=[data["creator"]] if data.get("creator") else [], documentation_url=f"https://www.openml.org/d/{dataset_id}", formats=[data["format"]] if data.get("format") else [], raw_reference="openml_fixture")


class UciAdapter(SourceAdapter):
    source_name, adapter_version = "uci", "1.0"
    def discover(self, query: str) -> str | None: return None
    def fetch_metadata(self, source_dataset_id: str) -> str: return f"https://archive.ics.uci.edu/dataset/{source_dataset_id}"
    def capability_report(self) -> dict[str, Any]: return {"metadata_discovery": False, "metadata_retrieval": True, "sample_retrieval": True, "viewer_access": False, "streaming": False, "authentication_required": False, "programmatic_access": "unknown_for_discovery", "rate_limits": "unknown", "bounded_sampling": True, "access_type": "controlled_seed_catalog", "sample_accessible": "conditional", "sampling_method": "public_flat_file_bounded_stream", "limitations": ["M0 did not establish a documented programmatic discovery endpoint"]}
    def access_policy(self) -> dict[str, Any]: return {"status": "public_direct_access_observed", "url": "https://uci-ics-mlr-prod.aws.uci.edu/privacy"}
    def normalize(self, raw: dict[str, Any], observed_at: str) -> CanonicalDataset:
        dataset_id, version = self.identify(raw)
        return self._record(raw=raw, observed_at=observed_at, dataset_id=dataset_id, version_id=version, name=raw.get("name"), url=raw.get("url"), description=raw.get("description"), tasks=raw.get("tasks"), modalities=raw.get("modalities"), tags=raw.get("tags") or [], sample_count=raw.get("sample_count"), class_count=raw.get("class_count"), license_claim=raw.get("license_claim"), documentation_url=raw.get("url"), formats=raw.get("formats") or [], raw_reference="uci_controlled_seed_fixture")


class KaggleAdapter(SourceAdapter):
    source_name, adapter_version = "kaggle", "1.0"
    def discover(self, query: str) -> str | None: return f"https://www.kaggle.com/api/v1/datasets/list?search={query}&pageSize=20"
    def fetch_metadata(self, source_dataset_id: str) -> str: return f"https://www.kaggle.com/api/v1/datasets/view/{source_dataset_id}"
    def capability_report(self) -> dict[str, Any]: return {"metadata_discovery": True, "metadata_retrieval": True, "sample_retrieval": False, "viewer_access": False, "streaming": False, "authentication_required": True, "programmatic_access": "metadata_only_under_m0_policy", "rate_limits": "unknown", "bounded_sampling": False, "access_type": "public_metadata_only", "sample_accessible": "unsupported_or_policy_limited", "sampling_method": None, "limitations": ["M0 observed metadata HTTP 403 for one record; no credentials or anonymous-download workaround"]}
    def access_policy(self) -> dict[str, Any]: return {"status": "metadata_only_no_credentials", "url": "https://www.kaggle.com/getting-started/524433"}
    def normalize(self, raw: dict[str, Any], observed_at: str) -> CanonicalDataset:
        dataset_id, version = self.identify(raw)
        return self._record(raw=raw, observed_at=observed_at, dataset_id=dataset_id, version_id=version, name=raw.get("title") or raw.get("ref"), url=f"https://www.kaggle.com/datasets/{dataset_id}", description=raw.get("subtitle"), tasks=raw.get("usabilityRating"), modalities=[], tags=[tag.get("name", tag) if isinstance(tag, dict) else tag for tag in raw.get("tags", [])], sample_count=None, license_claim=raw.get("licenseName"), creators=[raw["ownerName"]] if raw.get("ownerName") else [], documentation_url=f"https://www.kaggle.com/datasets/{dataset_id}", downloads=raw.get("totalDownloads"), stars=raw.get("voteCount"), formats=[item.get("name") for item in raw.get("datasetFiles", []) if item.get("name")], raw_reference="kaggle_fixture")


ADAPTERS = {"huggingface": HuggingFaceAdapter, "openml": OpenMLAdapter, "uci": UciAdapter, "kaggle": KaggleAdapter}
