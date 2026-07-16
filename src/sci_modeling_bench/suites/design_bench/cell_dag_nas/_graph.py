"""NASBench-101 31-token decoding and graph-invariant identity."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from numbers import Integral
from typing import Any

import numpy as np

ARCHITECTURE_LENGTH = 31
MAX_VERTICES = 7
MAX_EDGES = 9

START_TOKEN = 0
STOP_TOKEN = 1
PAD_TOKEN = 2
SEPARATOR_TOKEN = 3
INPUT_TOKEN = 4
OUTPUT_TOKEN = 5
CONV1X1_TOKEN = 6
CONV3X3_TOKEN = 7
MAXPOOL3X3_TOKEN = 8
NO_EDGE_TOKEN = 9
EDGE_TOKEN = 10

OPERATION_TOKENS = frozenset(
    {CONV1X1_TOKEN, CONV3X3_TOKEN, MAXPOOL3X3_TOKEN}
)
TOKEN_TO_HASH_LABEL = {
    INPUT_TOKEN: -1,
    OUTPUT_TOKEN: -2,
    CONV1X1_TOKEN: 1,
    CONV3X3_TOKEN: 0,
    MAXPOOL3X3_TOKEN: 2,
}


class ArchitectureEncodingError(ValueError):
    """A machine-readable failure while decoding one architecture."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class DecodedArchitecture:
    """Decoded NASBench-101 cell and its official-compatible identity."""

    tokens: tuple[int, ...]
    operations: tuple[int, ...]
    adjacency: tuple[tuple[int, ...], ...]
    canonical_hash: str

    @property
    def num_vertices(self) -> int:
        return len(self.operations)

    @property
    def num_edges(self) -> int:
        return sum(sum(row) for row in self.adjacency)


def decode_architecture(value: Any) -> DecodedArchitecture:
    """Decode and validate one Design-Bench NASBench token sequence."""

    if isinstance(value, (str, bytes, bytearray)):
        raise ArchitectureEncodingError(
            "invalid_architecture_type",
            "architecture must be a sequence of 31 integer tokens",
        )
    try:
        raw_tokens = tuple(value)
    except TypeError as exc:
        raise ArchitectureEncodingError(
            "invalid_architecture_type",
            "architecture must be a sequence of 31 integer tokens",
        ) from exc
    if len(raw_tokens) != ARCHITECTURE_LENGTH:
        raise ArchitectureEncodingError(
            "invalid_architecture_length",
            f"architecture must contain {ARCHITECTURE_LENGTH} tokens",
        )
    if any(isinstance(token, bool) or not isinstance(token, Integral) for token in raw_tokens):
        raise ArchitectureEncodingError(
            "non_integer_architecture_token",
            "architecture tokens must be integers",
        )
    tokens = tuple(int(token) for token in raw_tokens)
    if any(token < START_TOKEN or token > EDGE_TOKEN for token in tokens):
        raise ArchitectureEncodingError(
            "architecture_token_out_of_range",
            "architecture tokens must be in the inclusive range 0..10",
        )
    if tokens[0] != START_TOKEN:
        raise ArchitectureEncodingError(
            "missing_start_token",
            "architecture must begin with the start token",
        )

    separators = [index for index, token in enumerate(tokens) if token == SEPARATOR_TOKEN]
    if len(separators) != 1:
        raise ArchitectureEncodingError(
            "invalid_separator_count",
            "architecture must contain exactly one separator token",
        )
    separator = separators[0]
    num_vertices = separator - 1
    if not 2 <= num_vertices <= MAX_VERTICES:
        raise ArchitectureEncodingError(
            "invalid_vertex_count",
            f"architecture must encode between 2 and {MAX_VERTICES} vertices",
        )

    operations = tokens[1:separator]
    if operations[0] != INPUT_TOKEN or operations[-1] != OUTPUT_TOKEN:
        raise ArchitectureEncodingError(
            "invalid_endpoint_operations",
            "first and last graph operations must be input and output",
        )
    if any(token not in OPERATION_TOKENS for token in operations[1:-1]):
        raise ArchitectureEncodingError(
            "invalid_intermediate_operation",
            "intermediate operations must be conv1x1, conv3x3, or maxpool3x3",
        )

    edge_count = num_vertices * (num_vertices - 1) // 2
    edge_start = separator + 1
    edge_stop = edge_start + edge_count
    edge_tokens = tokens[edge_start:edge_stop]
    if len(edge_tokens) != edge_count or any(
        token not in (NO_EDGE_TOKEN, EDGE_TOKEN) for token in edge_tokens
    ):
        raise ArchitectureEncodingError(
            "invalid_adjacency_tokens",
            "adjacency must contain only no-edge and edge tokens",
        )
    if edge_stop >= len(tokens) or tokens[edge_stop] != STOP_TOKEN:
        raise ArchitectureEncodingError(
            "missing_stop_token",
            "architecture must contain a stop token immediately after adjacency",
        )
    if any(token != PAD_TOKEN for token in tokens[edge_stop + 1 :]):
        raise ArchitectureEncodingError(
            "invalid_padding_tokens",
            "all tokens after stop must be padding",
        )

    matrix = np.zeros((num_vertices, num_vertices), dtype=np.int8)
    matrix[np.triu_indices(num_vertices, k=1)] = np.asarray(edge_tokens) - NO_EDGE_TOKEN
    num_edges = int(matrix.sum())
    if num_edges > MAX_EDGES:
        raise ArchitectureEncodingError(
            "too_many_edges",
            f"architecture has {num_edges} edges; maximum is {MAX_EDGES}",
        )
    if not _is_full_dag(matrix):
        raise ArchitectureEncodingError(
            "non_full_dag",
            "every vertex must lie on a path from input to output",
        )

    labels = [TOKEN_TO_HASH_LABEL[token] for token in operations]
    return DecodedArchitecture(
        tokens=tokens,
        operations=operations,
        adjacency=tuple(tuple(int(value) for value in row) for row in matrix),
        canonical_hash=hash_module(matrix, labels),
    )


def hash_module(matrix: np.ndarray, labels: list[int]) -> str:
    """Return the graph-invariant hash used by NASBench-101."""

    vertices = matrix.shape[0]
    in_edges = np.sum(matrix, axis=0).tolist()
    out_edges = np.sum(matrix, axis=1).tolist()
    hashes = [
        hashlib.md5(str(item).encode("utf-8")).hexdigest()
        for item in zip(out_edges, in_edges, labels)
    ]
    for _ in range(vertices):
        next_hashes = []
        for vertex in range(vertices):
            incoming = [hashes[index] for index in range(vertices) if matrix[index, vertex]]
            outgoing = [hashes[index] for index in range(vertices) if matrix[vertex, index]]
            payload = (
                "".join(sorted(incoming))
                + "|"
                + "".join(sorted(outgoing))
                + "|"
                + hashes[vertex]
            )
            next_hashes.append(hashlib.md5(payload.encode("utf-8")).hexdigest())
        hashes = next_hashes
    return hashlib.md5(str(sorted(hashes)).encode("utf-8")).hexdigest()


def _is_full_dag(matrix: np.ndarray) -> bool:
    return not np.any(np.all(matrix[:-1, :] == 0, axis=1)) and not np.any(
        np.all(matrix[:, 1:] == 0, axis=0)
    )
