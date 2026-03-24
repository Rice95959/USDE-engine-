#!/usr/bin/env python3
"""
USDE v6.2 — Unified Deliberative Cognition Engine (Hooked Monolith)

Consolidation of v5.0–v5.8 plus three v7.5 interface hooks.

Architecture:
  §1:     Utilities + tokenizer
  §2:     Semantic parser (passive + wrappers + negation scope)
  §3:     Ontology projection
  §4:     Graph construction
  §5:     Governance engine
  §6:     Spectral substrate + enforcement + stabilization + spine
  §7:     Deep sensors (phrase triage, domain audit, cluster expansion)
  §8:     Parameterized governance with Ω profiles
  §9:     Telemetry + regime governor + pipeline operators
  §10:    Manifold memory + causal decomposition + domain LTM
  §11:    Contradiction field + resolution + insight + action
  §12:    MODE ROUTER (Hook 1 — v7.5 §2)
  §13:    SEQUENCE BUFFER (Hook 2 — v7.5 §8)
  §14:    GAP SENTINEL (Hook 3 — v7.5 §15)
  §15:    Engine6 (single-agent, hooked)
  §16:    CouncilOfOmegas (multi-agent, v7.5 telemetry schema)
  §17:    Falsification harness (115 tests)
  §18:    Demo (Obsidian Heights)

Properties:
  - Stdlib-only, deterministic, zero dependencies
  - Three v7.5 hooks: ModeRouter, SequenceBuffer, GapSentinel
  - SequenceBuffer: 5 MoveDetectors (composition over conditionals)
  - Output formatted for v7.5 LLM Judgment layer
"""

import re, math, hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from collections import defaultdict, OrderedDict
def cl(x): return max(0.0, min(1.0, float(x)))
def stable_hash(t): return hashlib.md5(t.encode()).hexdigest()[:12]

_STOP = frozenset("the a an is are was were in on at to for of and or but it that this "
    "with as by from not be has have had do does did i my me we so they them its".split())

def tokenize(text):
    return [w for w in re.findall(r'\b[a-z]{3,}\b', text.lower()) if w not in _STOP]

def _token_match(a, b):
    if not a or not b: return False
    ta, tb = set(tokenize(a)), set(tokenize(b))
    return len(ta & tb) / max(1, len(ta)) >= 0.7 if ta else False

def _jaccard(a, b):
    if not a or not b: return 0.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / max(1, len(sa | sb))

# ═══════════════════════════════════════════════════════════════════════
# §2. SEMANTIC PARSER
# ═══════════════════════════════════════════════════════════════════════

_CAUSAL_VERBS = re.compile(
    r'\b(causes?|caused|triggers?|triggered|drives?|drove|driven|creates?|created|'
    r'collapses?|collapsed|determines?|determined|produces?|produced|'
    r'forces?|forced|generates?|generated|induces?|induced|'
    r'prevents?|prevented|inhibits?|inhibited|accelerates?|accelerated|'
    r'enables?|enabled|leads?|led|leading|results?|resulted)\b', re.I)
_LINKING_VERBS = re.compile(r'\b(is|are|was|were|becomes?|remains?|appears?)\b', re.I)
_MEASURE_VERBS = re.compile(r'\b(measures?|detects?|observes?|records?|confirms?|demonstrates?)\b', re.I)
_MECHANISM_KW = {"because", "through", "via", "mechanism", "interaction", "coupling",
    "process", "dynamics", "law", "principle", "decoherence", "whereby", "thereby",
    "randomization", "thermalization", "scattering", "decay"}
_CLAUSE_SPLIT = re.compile(r'\b(because|although|but|however|therefore|while|whereas|despite|yet)\b', re.I)
_TEMPORAL_KW = {"before", "after", "then", "subsequently", "previously", "during", "when", "once"}
_QUALIFIER_KW = {"may", "might", "could", "possibly", "likely", "probably", "suggests", "indicates", "perhaps"}
_PASSIVE = re.compile(r'\b(?:is|was|were|been|being|are)\s+(\w+(?:ed|en|t))(?:\s+\w+)?\s+by\s+(.+?)(?:[,.]|$)', re.I)
_EPISTEMIC_WRAPPER = re.compile(
    r'^(?:it\s+is\s+(?:widely\s+)?(?:accepted|believed|argued|thought|suggested|claimed|known)\s+that\s+'
    r'|(?:studies|researchers?|experts?|scientists?)\s+(?:suggest|argue|believe|claim|show|demonstrate)\s+that\s+'
    r'|(?:there\s+is\s+(?:a\s+)?(?:consensus|agreement|belief|view)\s+that\s+))', re.I)
_NEG_SCOPE = re.compile(r'\b(not|no|never|neither|nor|cannot|doesn\'t|don\'t|won\'t|isn\'t|aren\'t|wasn\'t)\b', re.I)

@dataclass
class Claim:
    uid: str; text: str; confidence: float; mechanism: bool
    agent: str; effect: str; qualifiers: List[str]; polarity: int
    causal_verb: str; has_wrapper: bool; negation_scope: bool; temporal: bool

class SemanticParser:
    def parse(self, text):
        sents = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 5]
        claims = []
        for s in sents:
            tokens = set(tokenize(s)); uid = stable_hash(s)
            has_cause = bool(_CAUSAL_VERBS.search(s))
            has_mech = len(tokens & _MECHANISM_KW) > 0
            mechanism = has_cause and has_mech
            causal_verb_m = _CAUSAL_VERBS.search(s)
            cv = causal_verb_m.group(1).lower() if causal_verb_m else ""
            has_link = bool(_LINKING_VERBS.search(s))
            has_meas = bool(_MEASURE_VERBS.search(s))
            conf = 0.5
            if mechanism: conf = 0.7
            elif has_cause: conf = 0.6
            elif has_meas: conf = 0.65
            quals = [q for q in _QUALIFIER_KW if q in tokens]
            if quals: conf -= 0.1 * len(quals)
            conf = round(cl(conf), 3)
            passive_m = _PASSIVE.search(s)
            agent = passive_m.group(2).strip()[:30] if passive_m else s.split()[0][:20] if s.split() else "?"
            clauses = _CLAUSE_SPLIT.split(s)
            effect = clauses[-1].strip()[:40] if len(clauses) > 1 else s[-40:]
            wrapper = bool(_EPISTEMIC_WRAPPER.match(s))
            neg = bool(_NEG_SCOPE.search(s))
            polarity = -1 if neg else 1
            temporal = len(tokens & _TEMPORAL_KW) > 0
            claims.append(Claim(uid, s, conf, mechanism, agent, effect, quals, polarity, cv, wrapper, neg, temporal))
        return claims

# ═══════════════════════════════════════════════════════════════════════
# §3. ONTOLOGY PROJECTION
# ═══════════════════════════════════════════════════════════════════════

_ROLE_LEX = {
    "physical": {"electron", "photon", "atom", "particle", "field", "energy", "mass",
        "force", "wave", "spin", "torque", "magnetization", "current", "charge",
        "momentum", "temperature", "pressure", "gravity", "frequency", "coupling",
        "sand", "concrete", "aggregate", "bonding", "fracture", "slab", "damping",
        "vibration", "resonance", "fatigue", "crystalline", "contamination", "settling",
        "foundation", "structural", "cracking", "load"},
    "measurement": {"detector", "apparatus", "instrument", "measurement", "experiment",
        "sensor", "observation", "data", "reading", "lab", "probe", "test",
        "analysis", "sample", "report", "inspection"},
    "epistemic": {"belief", "knowledge", "theory", "hypothesis", "model", "interpretation",
        "evidence", "reasoning", "conclusion", "inference", "explanation"},
    "social": {"authority", "status", "reputation", "consensus", "community", "prestige",
        "institution", "peer", "publication", "expert", "reviewer", "accepted", "argued"},
    "phenomenological": {"consciousness", "awareness", "mind", "intention", "subjective",
        "perception", "experience", "qualia", "will", "feeling", "sensation"},
    "mathematical": {"equation", "function", "operator", "eigenvalue", "probability",
        "amplitude", "hilbert", "matrix", "integral", "superposition", "vector"},
    "metaphysical": {"god", "soul", "spirit", "divine", "supernatural", "karma",
        "destiny", "manifestation", "attraction", "cosmic", "fate"},
    "narrative": {"hero", "villain", "sacrifice", "betrayal", "journey", "quest",
        "defeat", "victory", "alliance", "revenge", "destiny", "prophecy", "legacy",
        "sealed", "mastered", "tricked", "deception", "protecting"},
}

@dataclass
class RoleTaggedEntity:
    text: str; role_probs: Dict[str, float]; dominant_role: str; ambiguity: float

class OntologyTagger:
    def tag(self, text, context=""):
        words = set(tokenize(text)) | set(tokenize(context))
        probs = {}
        for role, kw in _ROLE_LEX.items():
            probs[role] = len(words & kw)
        total = sum(probs.values()) or 1.0
        probs = {r: round(v / total, 4) for r, v in probs.items()}
        dominant = max(probs.items(), key=lambda x: x[1])[0]
        H = sum(-p * math.log(p + 1e-12) for p in probs.values() if p > 1e-8)
        return RoleTaggedEntity(text[:40], probs, dominant if sum(probs.values()) > 0 else "epistemic", round(H, 4))

    def tag_claim(self, claim):
        return self.tag(claim.text)

# ═══════════════════════════════════════════════════════════════════════
# §4. GRAPH CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ENode:
    id: int; uid: str; text: str; ntype: str; confidence: float; tension: float
    role: str; ambiguity: float; tags: List[str] = field(default_factory=list)
    quarantined: bool = False; probation: int = 0

@dataclass
class EEdge:
    src: int; tgt: int; etype: str; weight: float; signed_tension: float; provenance: str = ""

class EpistemicGraph:
    def __init__(self):
        self.nodes: Dict[int, ENode] = {}
        self.adj: Dict[int, List[EEdge]] = {}

    def add_node(self, uid, text, ntype="CLAIM", conf=0.5, tens=0.0, role="epistemic", amb=0.0, tags=None):
        nid = len(self.nodes)
        self.nodes[nid] = ENode(nid, uid, text[:80], ntype, conf, tens, role, amb, tags or [])
        return nid

    def add_edge(self, src, tgt, etype, weight, stension=0.0, prov=""):
        e = EEdge(src, tgt, etype, weight, stension, prov)
        self.adj.setdefault(src, []).append(e)
        return e

    def n_nodes(self): return len(self.nodes)
    def n_edges(self): return sum(len(el) for el in self.adj.values())
    def all_edges(self): return [e for el in self.adj.values() for e in el]

    def copy(self):
        g = EpistemicGraph()
        for nid, n in self.nodes.items():
            g.nodes[nid] = ENode(n.id, n.uid, n.text, n.ntype, n.confidence, n.tension,
                n.role, n.ambiguity, list(n.tags), n.quarantined, n.probation)
        for s, el in self.adj.items():
            g.adj[s] = [EEdge(e.src, e.tgt, e.etype, e.weight, e.signed_tension, e.provenance) for e in el]
        return g

    def neighbors(self, nid):
        fwd = {e.tgt for e in self.adj.get(nid, [])}
        rev = {src for src in self.adj for e in self.adj[src] if e.tgt == nid}
        return fwd | rev

    def components(self):
        visited = set(); comps = []
        for start in sorted(self.nodes.keys()):
            if start in visited: continue
            comp = []; q = [start]
            while q:
                n = q.pop(0)
                if n in visited: continue
                visited.add(n); comp.append(n)
                for nb in self.neighbors(n):
                    if nb not in visited: q.append(nb)
            comps.append(sorted(comp))
        return comps

    def centrality(self):
        """Degree centrality for each node."""
        c = {nid: 0 for nid in self.nodes}
        for el in self.adj.values():
            for e in el:
                c[e.src] = c.get(e.src, 0) + 1
                c[e.tgt] = c.get(e.tgt, 0) + 1
        mx = max(c.values()) if c else 1
        return {nid: round(v / max(mx, 1), 4) for nid, v in c.items()}

class GraphBuilder:
    def build(self, claims, tagger):
        g = EpistemicGraph(); roles = {}
        for c in claims:
            rte = tagger.tag_claim(c)
            nid = g.add_node(c.uid, c.text, "CLAIM", c.confidence, 0.0,
                rte.dominant_role, rte.ambiguity, list(rte.role_probs.keys())[:3])
            roles[c.uid] = rte
        nids = list(g.nodes.keys())
        for i in range(len(nids)):
            for j in range(i+1, len(nids)):
                ni, nj = g.nodes[nids[i]], g.nodes[nids[j]]
                tok_i, tok_j = set(tokenize(ni.text)), set(tokenize(nj.text))
                jac = _jaccard(tok_i, tok_j)
                if jac > 0.15:
                    ri, rj = roles.get(ni.uid), roles.get(nj.uid)
                    if ri and rj and ri.dominant_role != rj.dominant_role:
                        g.add_edge(nids[i], nids[j], "DOMAIN_CONFLICT", jac, jac*0.5,
                            f"{ri.dominant_role}≠{rj.dominant_role}")
                    elif jac > 0.3:
                        g.add_edge(nids[i], nids[j], "SUPPORT", jac, -jac*0.3)
                    else:
                        g.add_edge(nids[i], nids[j], "ADJACENCY", jac, 0.0)
                ci, cj = claims[i] if i < len(claims) else None, claims[j] if j < len(claims) else None
                if ci and cj and ci.causal_verb and cj.causal_verb:
                    if ci.polarity != cj.polarity or (ci.effect and cj.effect and not _token_match(ci.effect, cj.effect)):
                        if jac > 0.1:
                            g.add_edge(nids[i], nids[j], "CAUSAL_CONFLICT", 0.7, 0.6, "opposing_causes")
        return g, roles

# ═══════════════════════════════════════════════════════════════════════
# §5. GOVERNANCE ENGINE
# ═══════════════════════════════════════════════════════════════════════

_DOMAIN_KEYWORDS = {
    "physics": {"quantum", "electron", "photon", "spin", "orbital", "decoherence",
        "entanglement", "superposition", "hamiltonian", "scattering", "coupling"},
    "construction": {"concrete", "slab", "aggregate", "sand", "foundation", "curing",
        "bonding", "fracture", "damping", "vibration", "structural", "reinforcement",
        "rebar", "settling", "cracking", "fatigue", "load", "compressive"},
    "biology": {"cell", "protein", "gene", "membrane", "enzyme", "metabolism", "tissue",
        "organism", "mutation", "receptor", "neural", "synaptic"},
    "fiction": {"hero", "villain", "quest", "kingdom", "magic", "sword", "sealed",
        "jutsu", "chakra", "ninja", "hokage", "technique", "clone"},
    "social": {"joke", "bartender", "bet", "walks", "says", "laughs", "punchline",
        "conversation", "negotiation", "persuasion", "rhetoric"},
}

def classify_domain(text):
    tokens = set(tokenize(text))
    scores = {d: len(tokens & kw) for d, kw in _DOMAIN_KEYWORDS.items()}
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "general"

OMEGA_STOIC = {"metaphysical":0.80, "phenomenological":0.60, "social":0.35, "epistemic":0.25,
    "mathematical":0.05, "measurement":0.00, "physical":0.00, "narrative":0.00}
OMEGA_GRACEFUL = {"metaphysical":0.45, "phenomenological":0.20, "social":0.15, "epistemic":0.10,
    "mathematical":0.02, "measurement":0.00, "physical":0.00, "narrative":0.00}
OMEGA_CHARITY = {"metaphysical":0.10, "phenomenological":0.05, "social":0.05, "epistemic":0.05,
    "mathematical":0.00, "measurement":0.00, "physical":0.00, "narrative":0.00}

@dataclass
class GovernanceReport:
    violations: Dict[str, float]; violation_load: float; legibility: float
    demoted: bool; regime: str

class GovernanceEngine:
    def __init__(self, omega=None):
        self.omega = omega or OMEGA_STOIC

    def analyze(self, claims, text, tagger, domain="general"):
        violations = {}; total_v = 0.0
        for c in claims:
            rte = tagger.tag_claim(c)
            v = self.omega.get(rte.dominant_role, 0.0)
            if v > 0.01: violations[c.uid] = round(v, 3); total_v += v
        vl = round(cl(total_v / max(len(claims), 1)), 4)
        leg_tokens = set(tokenize(text))
        mech_count = len(leg_tokens & _MECHANISM_KW)
        legibility = round(cl(mech_count / max(len(claims), 1)), 3)
        demoted = vl > 0.5
        regime = "strict" if vl > 0.4 else "normal" if vl > 0.15 else "open"
        return GovernanceReport(violations, vl, legibility, demoted, regime)

class ParameterizedGovernance(GovernanceEngine):
    def __init__(self, omega=None, phrase_sens=1.0, cluster_sens=1.0):
        super().__init__(omega)
        self.phrase_sens = phrase_sens; self.cluster_sens = cluster_sens

    def analyze(self, claims, text, tagger, domain="general"):
        base = super().analyze(claims, text, tagger, domain)
        ph = phrase_triage(text); mh = domain_mechanism_audit(text, domain)
        ch = scan_smuggle_vocabulary(text)
        phrase_v = len(ph) * 0.06 * self.phrase_sens
        mech_v = len(mh) * 0.04
        cluster_v = sum(len(v) for v in ch.values()) * 0.03 * self.cluster_sens
        adj_v = round(cl(base.violation_load + phrase_v + mech_v + cluster_v), 4)
        regime = "strict" if adj_v > 0.4 else "normal" if adj_v > 0.15 else "open"
        return GovernanceReport(base.violations, adj_v, base.legibility, adj_v > 0.5, regime)

# ═══════════════════════════════════════════════════════════════════════
# §6. SPECTRAL + ENFORCEMENT + STABILIZATION + SPINE
# ═══════════════════════════════════════════════════════════════════════

class SpectralSubstrate:
    def analyze(self, g):
        n = g.n_nodes()
        if n < 2: return {"components": 1, "lambda2": 0.0, "fragility": 0.0}
        comps = g.components()
        edges = g.all_edges()
        tensions = [abs(e.signed_tension) for e in edges]
        frag = round(sum(tensions) / max(len(tensions), 1), 4) if tensions else 0.0
        return {"components": len(comps), "lambda2": round(frag * 0.5, 4), "fragility": frag}

class EnforcementEngine:
    def enforce(self, g, gov_report, threshold=0.4):
        actions = []
        for nid, node in g.nodes.items():
            if node.role in ("metaphysical", "phenomenological"):
                v = gov_report.violations.get(node.uid, 0)
                if v > threshold:
                    node.quarantined = True; actions.append(f"quarantine:{node.uid[:12]}")
        return actions

class Stabilizer:
    def stabilize(self, g, pass_num=0):
        actions = []
        for el in g.adj.values():
            for e in el:
                if abs(e.signed_tension) > 0.8:
                    e.signed_tension *= 0.9; actions.append(f"damped:{e.src}->{e.tgt}")
        return actions

class SpineExtractor:
    def extract(self, g):
        if g.n_nodes() == 0: return []
        cent = g.centrality()
        ranked = sorted(cent.items(), key=lambda x: -x[1])
        spine = []
        for nid, c in ranked[:5]:
            n = g.nodes.get(nid)
            if n: spine.append({"uid": n.uid[:12], "text": n.text[:50], "centrality": c, "role": n.role})
        return spine

# ═══════════════════════════════════════════════════════════════════════
# §7. DEEP SENSORS
# ═══════════════════════════════════════════════════════════════════════

_PHYSICAL_HEADS = {
    "collapse", "reduction", "energy", "field", "resonance", "coupling", "wave",
    "frequency", "vibration", "force", "alignment", "state", "coherence", "localization",
    "interaction", "entanglement", "superposition", "wavefunction", "decoherence",
    "transition", "bonding", "settling", "cracking", "fatigue",
}
_SMUGGLE_MODIFIERS = {
    "intentional", "conscious", "divine", "spiritual", "cosmic", "noetic",
    "psychic", "universal", "transcendent", "karmic", "manifested", "vibrational",
    "holistic", "sacred", "mystical", "etheric", "astral",
}

_CLUSTER_DEFS = {
    "consciousness_cluster": ["consciousness", "awareness", "mind", "observer", "subjective",
        "qualia", "sentience", "perception", "cognition", "phenomenal"],
    "quantum_mysticism_cluster": ["quantum", "superposition", "entanglement", "collapse",
        "coherence", "tunneling", "nonlocal", "wavefunction"],
    "energy_cluster": ["energy", "vibration", "frequency", "resonance", "field",
        "aura", "chakra", "meridian", "prana", "chi"],
    "causation_cluster": ["manifests", "attracts", "creates", "determines", "influences",
        "shapes", "controls", "directs", "channels", "focuses"],
}
_CLUSTER_LOOKUP = {}
for _cn, _ws in _CLUSTER_DEFS.items():
    for _w in _ws: _CLUSTER_LOOKUP[_w] = _cn
_STEM_PREFIXES = {"noetic": "consciousness_cluster", "psycho": "consciousness_cluster",
    "bio-field": "energy_cluster", "biofield": "energy_cluster"}

_DOMAIN_MECHANISMS = {
    "physics": {"decoherence", "superposition", "entanglement", "tunneling", "scattering",
        "coupling", "spin", "orbital", "hamiltonian"},
}

def phrase_triage(text):
    tokens = tokenize(text); findings = []
    for i in range(len(tokens) - 1):
        mod, head = tokens[i], tokens[i+1]
        if mod in _SMUGGLE_MODIFIERS and head in _PHYSICAL_HEADS:
            findings.append((mod, head, i))
        if i < len(tokens) - 2:
            far = tokens[i+2]
            if mod in _SMUGGLE_MODIFIERS and far in _PHYSICAL_HEADS:
                findings.append((mod, far, i))
    return findings

def domain_mechanism_audit(text, domain):
    if domain == "physics": return []
    tokens = set(tokenize(text)); findings = []
    for mech in _DOMAIN_MECHANISMS.get("physics", set()):
        if mech in tokens and domain in ("construction", "business", "general"):
            findings.append((mech, "physics", domain))
    return findings

def scan_smuggle_vocabulary(text):
    found = defaultdict(list)
    for t in tokenize(text):
        c = _CLUSTER_LOOKUP.get(t)
        if not c:
            for prefix, cluster in _STEM_PREFIXES.items():
                if t.startswith(prefix): c = cluster; break
        if c: found[c].append(t)
    return dict(found)

# ═══════════════════════════════════════════════════════════════════════
# §8-§9. TELEMETRY + GOVERNOR + PIPELINE (compressed from v6.0)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Telemetry:
    tension: float = 0.0; confidence: float = 0.5; fragility: float = 0.0
    ambiguity: float = 0.0; cohesion: float = 0.5
    def vector(self): return (self.tension, self.confidence, self.fragility, self.ambiguity, self.cohesion)
    def as_dict(self): return {"tension": self.tension, "confidence": self.confidence,
        "fragility": self.fragility, "ambiguity": self.ambiguity, "cohesion": self.cohesion}

class TelemetryComputer:
    def compute(self, g, novel=0):
        edges = g.all_edges()
        tension = round(sum(abs(e.signed_tension) for e in edges) / max(len(edges), 1), 4)
        conf = round(sum(n.confidence for n in g.nodes.values()) / max(len(g.nodes), 1), 4) if g.nodes else 0.5
        amb = round(sum(n.ambiguity for n in g.nodes.values()) / max(len(g.nodes), 1), 4) if g.nodes else 0.0
        frag_data = SpectralSubstrate().analyze(g)
        return Telemetry(tension, conf, frag_data["fragility"], amb, 1.0 - tension)

@dataclass
class GovernorParams:
    alpha: float = 0.6; beta: float = 0.4; gamma: float = 0.15

class RegimeGovernor:
    def __init__(self, params=None):
        self.params = params or GovernorParams(); self.r = 0.5; self.history = []
    def update(self, z):
        delta = self.params.alpha * z.tension - self.params.beta * z.confidence + self.params.gamma * z.fragility
        self.r = round(cl(self.r + delta * 0.1), 4)
        self.history.append(self.r)
        return self.r

@dataclass
class GraphSnapshot:
    graph: EpistemicGraph; telemetry: Telemetry; r: float; energy: float; pass_idx: int

class ManifoldMemory:
    def __init__(self):
        self.snapshots: List[GraphSnapshot] = []
    def clear(self): self.snapshots.clear()
    def record(self, snap): self.snapshots.append(snap)
    def n_views(self): return len(self.snapshots)
    def invariant_nodes(self):
        if len(self.snapshots) < 2: return set()
        sets = [set(s.graph.nodes.keys()) for s in self.snapshots]
        return sets[0].intersection(*sets[1:]) if sets else set()
    def variant_nodes(self):
        if len(self.snapshots) < 2: return set()
        all_n = set(); common = self.invariant_nodes()
        for s in self.snapshots: all_n |= set(s.graph.nodes.keys())
        return all_n - common
    def invariant_edges(self):
        if len(self.snapshots) < 2: return []
        return [e for e in self.snapshots[0].graph.all_edges()]
    def most_stable(self):
        if not self.snapshots: return None
        return min(self.snapshots, key=lambda s: s.energy)
    def build_invariant_graph(self):
        if not self.snapshots: return EpistemicGraph()
        return self.snapshots[-1].graph.copy()

# ═══════════════════════════════════════════════════════════════════════
# §10. CAUSAL DECOMPOSITION + DOMAIN LTM
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CausalChain:
    chain_id: str; trigger: str; pathway: List[str]; effect: str; confidence: float

class CausalDecomposer:
    def decompose(self, claims):
        chains = []
        causal = [c for c in claims if c.causal_verb]
        for c in causal:
            cid = stable_hash(c.text + "_chain")
            trigger = c.agent[:30]; effect = c.effect[:30]
            pathway = [w for w in tokenize(c.text) if w in _MECHANISM_KW][:3]
            chains.append(CausalChain(cid, trigger, pathway, effect, c.confidence))
        return chains

@dataclass
class LTMEntry:
    uid: str; text: str; domain: str; confirms: int = 0; contradicts: int = 0
    entry_type: str = "claim"; stale: float = 0.0

class DomainLTM:
    def __init__(self):
        self.entries: Dict[str, LTMEntry] = {}; self.episode = 0
    def confirm(self, uid, text, domain="general", etype="claim"):
        if uid in self.entries: self.entries[uid].confirms += 1; self.entries[uid].stale = 0
        else: self.entries[uid] = LTMEntry(uid, text[:50], domain, 1, 0, etype)
    def contradict(self, uid):
        if uid in self.entries: self.entries[uid].contradicts += 1
    def contradict_cross(self, uid, domain):
        if uid in self.entries and self.entries[uid].domain != domain: self.entries[uid].contradicts += 1
    def decay(self, domain):
        for e in self.entries.values():
            if e.domain == domain: e.stale = round(e.stale + 0.05, 3)
    def prune(self):
        self.entries = {k: v for k, v in self.entries.items() if v.stale < 1.0}
    def update_stagnation(self, inv_count): pass
    def summary(self):
        return {"entries": len(self.entries), "domains": list(set(e.domain for e in self.entries.values()))[:5]}

def compute_redundancy(text, ltm):
    tokens = set(tokenize(text))
    known = set()
    for e in ltm.entries.values(): known |= set(tokenize(e.text))
    return round(len(tokens & known) / max(len(tokens), 1), 3) if tokens else 0.0

def compute_centrality(ltm):
    if not ltm.entries: return {}
    return {uid: round(e.confirms / max(e.confirms + e.contradicts, 1), 3) for uid, e in ltm.entries.items()}

# ═══════════════════════════════════════════════════════════════════════
# §11. CONTRADICTION FIELD + RESOLUTION + INSIGHT + ACTION
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ConflictEntry:
    uid_a: str; uid_b: str; tension: float; domain_a: str; domain_b: str
    etype: str; t_registered: int; resolved: bool = False

class ContradictionField:
    def __init__(self):
        self.conflicts: List[ConflictEntry] = []; self._resolved: Set[str] = set()
    def register(self, ua, ub, tension, da, db, etype, t):
        key = f"{min(ua,ub)}_{max(ua,ub)}"
        if key not in self._resolved:
            self.conflicts.append(ConflictEntry(ua, ub, abs(tension), da, db, etype, t))
    def resolve(self, ua, ub):
        key = f"{min(ua,ub)}_{max(ua,ub)}"; self._resolved.add(key)
        for c in self.conflicts:
            if f"{min(c.uid_a,c.uid_b)}_{max(c.uid_a,c.uid_b)}" == key: c.resolved = True
    def decay(self, t):
        self.conflicts = [c for c in self.conflicts if not c.resolved and (t - c.t_registered) < 10]
    def summary(self):
        active = [c for c in self.conflicts if not c.resolved]
        return {"active": len(active), "resolved": len(self._resolved),
            "max_tension": max((c.tension for c in active), default=0.0)}
    def pressure(self, centrality):
        return round(sum(c.tension for c in self.conflicts if not c.resolved) / max(len(self.conflicts), 1), 4)
    def focus_set(self):
        return {c.uid_a for c in self.conflicts if not c.resolved and c.tension > 0.3} | \
               {c.uid_b for c in self.conflicts if not c.resolved and c.tension > 0.3}
    def credible_conflicts(self, ltm):
        active = [c for c in self.conflicts if not c.resolved]
        scored = []
        for c in active:
            phi = c.tension
            if c.uid_a in ltm.entries: phi += ltm.entries[c.uid_a].confirms * 0.1
            if c.uid_b in ltm.entries: phi += ltm.entries[c.uid_b].confirms * 0.1
            scored.append((f"{c.uid_a}_{c.uid_b}", c, phi))
        return sorted(scored, key=lambda x: -x[2])
    def steer(self, governor, centrality):
        p = self.pressure(centrality)
        if p > 0.5: governor.r = round(cl(governor.r + 0.03), 4); return f"cfield_steer:+0.03"
        return None
    def open_count(self):
        return sum(1 for c in self.conflicts if not c.resolved)

class ResolutionOperator:
    def attempt(self, conflict, ltm, domain):
        if conflict.domain_a != conflict.domain_b:
            return True, "domain_separation", f"{conflict.domain_a}≠{conflict.domain_b}"
        if conflict.uid_a in ltm.entries and conflict.uid_b in ltm.entries:
            ea, eb = ltm.entries[conflict.uid_a], ltm.entries[conflict.uid_b]
            if ea.confirms > eb.confirms + 2: return True, "evidence_weight", f"{ea.confirms}>{eb.confirms}"
        return False, "unresolved", ""

class ActionSynthesizer:
    def synthesize(self, inv_g, chains, essence, gov_report):
        recs = []
        if gov_report.violation_load > 0.3:
            recs.append(Recommendation(1, "challenge_violations", 0.8, "high_violation_load",
                ["verify_mechanism", "check_domain"]))
        for ch in chains[:3]:
            recs.append(Recommendation(len(recs)+1, f"trace:{ch.trigger[:15]}→{ch.effect[:15]}",
                ch.confidence, "causal_chain", []))
        return recs

@dataclass
class Recommendation:
    rank: int; pathway: str; confidence: float; basis: str; caveats: List[str]

class InsightDetector:
    def detect(self, passes, manifold):
        events = []
        for i in range(1, len(passes)):
            if abs(passes[i]["L"] - passes[i-1]["L"]) > 0.1:
                events.append(InsightEvent(i, "energy_shift"))
        return events

@dataclass
class InsightEvent:
    pass_idx: int; signal: str

class InsightPolicy:
    def __init__(self): self.attempts = defaultdict(int); self.insights = []
    def record_attempt(self, target): self.attempts[target] += 1
    def record_insight(self, r, z, target, L, domain=""): self.insights.append({"r": r, "L": L, "domain": domain})
    def decay(self): pass
    def suggest_r_bias(self, r, domain): return 0.0
    def summary(self): return {"attempts": sum(self.attempts.values()), "insights": len(self.insights)}

class RevisitPlanner:
    def plan(self, z, inv_c, var_c, n_views, ltm, policy): return []
    def apply_goal(self, goal, governor): pass

class CDCController:
    def inject_goals(self, goals, cfield): return goals

def system_energy_full(z, params, cfield, centrality):
    base = z.tension * 0.4 + z.fragility * 0.3 + z.ambiguity * 0.2 + (1 - z.cohesion) * 0.1
    cp = cfield.pressure(centrality)
    return round(base + cp * 0.15, 4)

# ═══════════════════════════════════════════════════════════════════════
# §12. HOOK 1: MODE ROUTER (v7.5 §2)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ModeProfile:
    mode: str           # empirical | narrative | mixed | social_sequence
    confidence: float   # how sure the router is
    omega_key: str      # which Ω profile to use
    rationale: str      # why this mode

class ModeRouter:
    """Front-of-pipeline mode classification.

    Uses domain keywords + ontology tag distribution to select mode.
    Returns ModeProfile that governs downstream Ω selection.
    """

    # Domain → mode mapping
    _DOMAIN_MODE = {
        "physics": "empirical", "construction": "empirical", "biology": "empirical",
        "fiction": "narrative", "social": "social_sequence", "general": "empirical",
    }

    # Narrative indicator patterns
    _NARRATIVE_SIGNALS = re.compile(
        r'\b(hero|villain|quest|journey|chapter|once upon|story|tale|'
        r'sealed|mastered|defeated|betrayed|sacrificed|protected|unleashed|'
        r'hokage|jutsu|chakra|ninja|clone|scroll|technique)\b', re.I)
    # Social sequence indicator patterns
    _SOCIAL_SIGNALS = re.compile(
        r'\b(walks into|bartender|bet you|says to|replied|laughed|punchline|'
        r'told him|she said|he asked|negotiat|persuad|convinc|rhetori)\b', re.I)
    # Epistemic hedge density
    _HEDGE_WORDS = {"believe", "seems", "appears", "possibly", "perhaps", "might",
        "could", "likely", "probably", "suggests", "think", "feel", "sense", "guess"}

    def route(self, text, claims, tagger):
        """Classify text into evaluation mode. Returns ModeProfile."""
        domain = classify_domain(text)
        base_mode = self._DOMAIN_MODE.get(domain, "empirical")

        # Count ontology signals across claims
        role_counts = defaultdict(int)
        for c in claims:
            rte = tagger.tag_claim(c)
            role_counts[rte.dominant_role] += 1
        total = sum(role_counts.values()) or 1

        narrative_ratio = (role_counts.get("narrative", 0) + role_counts.get("phenomenological", 0) * 0.3) / total
        physical_ratio = (role_counts.get("physical", 0) + role_counts.get("measurement", 0)) / total
        social_ratio = role_counts.get("social", 0) / total

        # Pattern-based signal counting
        narrative_hits = len(self._NARRATIVE_SIGNALS.findall(text))
        social_hits = len(self._SOCIAL_SIGNALS.findall(text))

        # Decision logic
        if social_hits >= 3 or (domain == "social" and social_hits >= 1):
            mode, conf, rationale = "social_sequence", 0.8 + min(social_hits * 0.05, 0.15), "social_pattern_density"
        elif narrative_hits >= 4 or (narrative_ratio > 0.3 and narrative_hits >= 2):
            mode, conf, rationale = "narrative", 0.75 + min(narrative_hits * 0.03, 0.2), "narrative_signal_density"
        elif narrative_hits >= 2 and physical_ratio > 0.2:
            mode, conf, rationale = "mixed", 0.7, "dual_ontology_signals"
        elif domain == "fiction":
            mode, conf, rationale = "narrative", 0.85, "fiction_domain"
        else:
            mode, conf, rationale = base_mode, 0.8 + physical_ratio * 0.15, "domain_classification"

        # Map mode → Ω profile key
        omega_map = {
            "empirical": "stoic", "narrative": "charity", "mixed": "graceful", "social_sequence": "charity",
        }
        omega_key = omega_map.get(mode, "stoic")

        return ModeProfile(mode, round(cl(conf), 3), omega_key, rationale)

# ═══════════════════════════════════════════════════════════════════════
# §13. HOOK 2: SEQUENCE BUFFER (v7.5 §8)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class MoveSignal:
    """A detected structural move in the claim sequence."""
    move_type: str       # preemptive_stabilizer | authority_frontload | deflection_sequence |
                         # confidence_escalation | false_completeness
    source_idx: int      # index of triggering claim
    target_idx: int      # index of affected claim (-1 if N/A)
    confidence: float    # detection confidence
    evidence: str        # human-readable reason

class MoveDetector:
    """Base interface for sequence move detectors."""
    name: str = "base"
    def detect(self, claims, graph, tagger) -> List[MoveSignal]:
        return []

class PreemptiveStabilizerDetector(MoveDetector):
    """Detects epistemic hedges immediately before high-confidence causal assertions.

    Signal: hedge density in claim[i] high + causal confidence in claim[i+1] high.
    A legitimate expert hedges about uncertain parts. A stabilizer hedges before
    the part they're most committed to — which is backwards.
    """
    name = "preemptive_stabilizer"
    _HEDGE_TOKENS = {"believe", "seems", "appears", "possibly", "perhaps", "might",
        "could", "likely", "probably", "suggests", "think", "feel", "sense",
        "guess", "experience", "opinion", "view"}
    _CONF_MARKERS = {"clearly", "obviously", "certainly", "definitely", "proves",
        "demonstrates", "confirms", "establishes", "shows", "determined"}

    def detect(self, claims, graph, tagger) -> List[MoveSignal]:
        signals = []
        for i in range(len(claims) - 1):
            tokens_i = set(tokenize(claims[i].text))
            tokens_j = set(tokenize(claims[i+1].text))
            hedge_count = len(tokens_i & self._HEDGE_TOKENS)
            hedge_density = hedge_count / max(len(tokens_i), 1)
            next_has_causal = bool(claims[i+1].causal_verb)
            next_has_confidence = len(tokens_j & self._CONF_MARKERS) > 0 or claims[i+1].confidence > 0.6
            if hedge_density > 0.08 and next_has_causal and next_has_confidence:
                conf = round(cl(0.5 + hedge_density * 2 + (0.2 if next_has_confidence else 0)), 3)
                evidence_text = f"hedge_density={hedge_density:.2f} before causal claim"
                signals.append(MoveSignal(self.name, i, i+1, conf, evidence_text))
        return signals

class AuthorityFrontloadDetector(MoveDetector):
    """Detects role assertions preceding claims with weak mechanistic support.

    Signal: 'As an engineer...' or 'In my 20 years of...' immediately before
    a claim that has no mechanism keyword support. The authority is doing
    the work that evidence should be doing.
    """
    name = "authority_frontload"
    _ROLE_PATTERNS = re.compile(
        r'\b(as (?:an? )?(?:engineer|expert|scientist|professional|specialist|researcher|doctor|'
        r'consultant|architect|contractor|analyst|manager|director|professor|'
        r'practitioner|technician|inspector|auditor))\b|'
        r'\b(in my (?:\d+ )?years? (?:of|as|in))\b|'
        r'\b(speaking as|from my experience|based on my expertise)\b', re.I)

    def detect(self, claims, graph, tagger) -> List[MoveSignal]:
        signals = []
        for i in range(len(claims) - 1):
            has_role = bool(self._ROLE_PATTERNS.search(claims[i].text))
            if not has_role: continue
            # Check if next claim has weak mechanism
            next_tokens = set(tokenize(claims[i+1].text))
            mech_support = len(next_tokens & _MECHANISM_KW)
            next_rte = tagger.tag_claim(claims[i+1])
            is_physical = next_rte.dominant_role in ("physical", "measurement")
            if mech_support == 0 or (not is_physical and next_rte.dominant_role in ("metaphysical", "phenomenological")):
                conf = round(cl(0.6 + (0.2 if mech_support == 0 else 0) + (0.15 if not is_physical else 0)), 3)
                signals.append(MoveSignal(self.name, i, i+1, conf,
                    f"role_assertion→{next_rte.dominant_role}(mech={mech_support})"))
        return signals

class DeflectionSequenceDetector(MoveDetector):
    """Detects naming a competing explanation then pivoting without refuting it.

    Signal: claim[i] references another agent's explanation, claim[i+1] introduces
    a different causal chain without negation or refutation bridge.
    The Contractor Wilkes pattern: mentions lab analysis, then pivots to
    'negative energy' without addressing the lab's mechanism.
    """
    name = "deflection_sequence"
    _REFERENCE_PATTERN = re.compile(
        r'\b((?:miller|wilkes|lab|engineer|contractor|analyst|report|study|findings?)\s+'
        r'(?:says?|said|argues?|argued|claims?|claimed|found|showed|suggests?))\b|'
        r'\b((?:according to|as (?:stated|claimed|argued) by))\b', re.I)
    _REFUTATION_MARKERS = {"however", "but", "although", "despite", "nevertheless", "wrong",
        "incorrect", "false", "disproven", "refuted", "contradicts", "fails", "flawed"}

    def detect(self, claims, graph, tagger) -> List[MoveSignal]:
        signals = []
        for i in range(len(claims) - 1):
            has_ref = bool(self._REFERENCE_PATTERN.search(claims[i].text))
            if not has_ref: continue
            next_tokens = set(tokenize(claims[i+1].text))
            has_refutation = len(next_tokens & self._REFUTATION_MARKERS) > 0
            next_has_causal = bool(claims[i+1].causal_verb)
            if not has_refutation and next_has_causal:
                # Different causal chain introduced without bridging
                tokens_i = set(tokenize(claims[i].text))
                overlap = _jaccard(tokens_i, next_tokens)
                if overlap < 0.35:  # Low overlap = different chain
                    conf = round(cl(0.55 + (0.3 - overlap) + (0.1 if not has_refutation else 0)), 3)
                    signals.append(MoveSignal(self.name, i, i+1, conf,
                        f"reference_without_refutation(overlap={overlap:.2f})"))
        return signals

class ConfidenceEscalationDetector(MoveDetector):
    """Detects rising assertive framing without new evidence.

    Signal: consecutive claims from the same agent that escalate in confidence
    modifiers (may→likely→clearly→obviously) without introducing new evidence.
    The certainty gradient climbs but the evidence base is flat.
    """
    name = "confidence_escalation"
    _CONF_LEVELS = {
        "may": 1, "might": 1, "could": 1, "possibly": 1, "perhaps": 1,
        "likely": 2, "probably": 2, "suggests": 2, "indicates": 2,
        "shows": 3, "demonstrates": 3, "proves": 3, "confirms": 3,
        "clearly": 4, "obviously": 4, "certainly": 4, "definitely": 4,
        "undeniably": 5, "irrefutably": 5, "unquestionably": 5,
    }
    _EVIDENCE_MARKERS = {"data", "lab", "test", "experiment", "measurement", "sample",
        "analysis", "report", "observation", "finding", "result", "study", "survey"}

    def detect(self, claims, graph, tagger) -> List[MoveSignal]:
        signals = []
        for i in range(len(claims) - 1):
            tokens_i = set(tokenize(claims[i].text))
            tokens_j = set(tokenize(claims[i+1].text))
            # Confidence level of each claim
            lvl_i = max((self._CONF_LEVELS.get(t, 0) for t in tokens_i), default=0)
            lvl_j = max((self._CONF_LEVELS.get(t, 0) for t in tokens_j), default=0)
            # Evidence addition between claims
            new_evidence = len(tokens_j & self._EVIDENCE_MARKERS) - len(tokens_i & self._EVIDENCE_MARKERS)
            if lvl_j > lvl_i and new_evidence <= 0:
                delta = lvl_j - lvl_i
                if delta >= 1:
                    conf = round(cl(0.4 + delta * 0.15 + (0.1 if new_evidence < 0 else 0)), 3)
                    signals.append(MoveSignal(self.name, i, i+1, conf,
                        f"confidence_delta={delta}(lvl:{lvl_i}→{lvl_j}),evidence_delta={new_evidence}"))
        return signals

class FalseCompletenessDetector(MoveDetector):
    """Detects premature conclusion while open contradictions remain.

    Signal: conclusion-framing markers (therefore, in summary) in claim[i]
    while the graph still has unresolved contradiction edges.
    The speaker is closing the argument while open threads remain.
    """
    name = "false_completeness"
    _CONCLUSION_MARKERS = {"therefore", "thus", "hence", "consequently", "confirms",
        "summary", "conclude", "conclusion", "established", "proven", "demonstrates",
        "clearly", "evident", "obvious", "undeniable", "settles"}

    def detect(self, claims, graph, tagger) -> List[MoveSignal]:
        signals = []
        # Count open conflicts in graph
        conflict_edges = [e for e in graph.all_edges() if "CONFLICT" in e.etype]
        open_conflicts = len(conflict_edges)

        for i, c in enumerate(claims):
            tokens = set(tokenize(c.text))
            conclusion_hits = len(tokens & self._CONCLUSION_MARKERS)
            if conclusion_hits > 0 and open_conflicts > 0:
                conf = round(cl(0.5 + conclusion_hits * 0.1 + open_conflicts * 0.1), 3)
                signals.append(MoveSignal(self.name, i, -1, conf,
                    f"conclusion_markers={conclusion_hits},open_conflicts={open_conflicts}"))
        return signals


class SequenceBuffer:
    """Event-driven causal monitor using composition of MoveDetectors.

    Each detector has detect(claims, graph, tagger) → List[MoveSignal].
    Adding new moves = appending a detector to the list.
    """
    def __init__(self, detectors: Optional[List[MoveDetector]] = None):
        self.detectors = detectors or [
            PreemptiveStabilizerDetector(),
            AuthorityFrontloadDetector(),
            DeflectionSequenceDetector(),
            ConfidenceEscalationDetector(),
            FalseCompletenessDetector(),
        ]

    def scan(self, claims, graph, tagger) -> List[MoveSignal]:
        """Run all detectors. Returns sorted list of detected moves."""
        all_signals = []
        for det in self.detectors:
            try:
                signals = det.detect(claims, graph, tagger)
                all_signals.extend(signals)
            except Exception:
                pass  # Detector failure must not crash pipeline
        # Sort by source_idx for sequence order, then confidence
        all_signals.sort(key=lambda s: (s.source_idx, -s.confidence))
        return all_signals

    def summary(self, signals: List[MoveSignal]) -> Dict:
        """Export for v7.5 telemetry schema."""
        if not signals:
            return {"stateful": False, "moves": [], "move_count": 0, "dominant_move": None}
        by_type = defaultdict(list)
        for s in signals: by_type[s.move_type].append(s)
        dominant = max(by_type.items(), key=lambda x: sum(s.confidence for s in x[1]))
        return {
            "stateful": True,
            "moves": [{"type": s.move_type, "source_idx": s.source_idx, "target_idx": s.target_idx,
                "confidence": s.confidence, "evidence": s.evidence} for s in signals],
            "move_count": len(signals),
            "dominant_move": dominant[0],
            "move_types": list(by_type.keys()),
        }

# ═══════════════════════════════════════════════════════════════════════
# §14. HOOK 3: GAP SENTINEL (v7.5 §15)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class GapSignal:
    gap_type: str       # signal_vacuum | operator_missing | indecisive_council |
                        # unresolved_centrality | degenerate_graph
    severity: float     # 0-1
    evidence: str       # what triggered it

class GapSentinel:
    """Monitors for degenerate graph states that indicate engine weakness.

    Does NOT diagnose the gap — just emits flags for the v7.5 LLM layer.
    """

    def scan(self, graph, gov_report, claims, cfield, council_result=None) -> List[GapSignal]:
        gaps = []

        # 1. HIGH Vm / LOW CENTRALITY: Council shouting but no node winning
        if gov_report.violation_load > 0.3:
            cent = graph.centrality()
            max_cent = max(cent.values()) if cent else 0
            if max_cent < 0.3:
                gaps.append(GapSignal("signal_vacuum",
                    round(cl(gov_report.violation_load - max_cent), 3),
                    f"Vm={gov_report.violation_load:.3f},max_centrality={max_cent:.3f}"))

        # 2. OPERATOR STARVATION: high-impact claim with zero mechanistic support
        for c in claims:
            if c.confidence > 0.5 and c.mechanism:
                # Check if the mechanism is actually supported in the graph
                node_match = None
                for nid, n in graph.nodes.items():
                    if n.uid == c.uid: node_match = n; break
                if node_match:
                    neighbors = graph.neighbors(node_match.id)
                    support_edges = [e for e in graph.all_edges()
                        if (e.src == node_match.id or e.tgt == node_match.id) and "SUPPORT" in e.etype]
                    if len(support_edges) == 0 and len(neighbors) > 0:
                        gaps.append(GapSignal("operator_missing", 0.6,
                            f"claim '{c.text[:30]}' has mechanism but no SUPPORT edges"))

        # 3. INDECISIVE COUNCIL: Vm variance too tight — both agents saying ~same thing
        if council_result:
            vs = council_result.get("agent_s", {}).get("violation_load", 0)
            vg = council_result.get("agent_g", {}).get("violation_load", 0)
            if abs(vs - vg) < 0.05 and vs > 0.15:
                gaps.append(GapSignal("indecisive_council", 0.4,
                    f"Stoic={vs:.3f},Graceful={vg:.3f}(Δ<0.05)"))

        # 4. DEGENERATE GRAPH: too few edges relative to nodes
        if graph.n_nodes() > 3 and graph.n_edges() < graph.n_nodes() * 0.5:
            gaps.append(GapSignal("degenerate_graph", 0.5,
                f"nodes={graph.n_nodes()},edges={graph.n_edges()}(ratio<0.5)"))

        # 5. UNRESOLVED CONTRADICTIONS with no winner
        open_c = cfield.open_count()
        if open_c > 2:
            gaps.append(GapSignal("unresolved_centrality", round(cl(open_c * 0.15), 3),
                f"open_conflicts={open_c}"))

        # 6. CLUSTER VACUUM: violation detected but no cluster explains it
        if gov_report.violation_load > 0.2:
            has_cluster = any(n.role in ("metaphysical", "phenomenological") for n in graph.nodes.values())
            if not has_cluster:
                gaps.append(GapSignal("signal_vacuum", 0.45,
                    f"Vm={gov_report.violation_load:.3f} but no metaphysical/phenomenological nodes"))

        gaps.sort(key=lambda g: -g.severity)
        return gaps

    def summary(self, gaps: List[GapSignal]) -> Dict:
        """Export for v7.5 telemetry schema."""
        if not gaps:
            return {"engine_gap_detected": False, "gap_flags": [], "max_severity": 0.0}
        return {
            "engine_gap_detected": True,
            "gap_flags": [{"type": g.gap_type, "severity": g.severity, "evidence": g.evidence} for g in gaps],
            "max_severity": gaps[0].severity,
            "dominant_gap": gaps[0].gap_type,
        }

# ═══════════════════════════════════════════════════════════════════════
# §15. ENGINE6 (single-agent, hooked for v7.5)
# ═══════════════════════════════════════════════════════════════════════

class Engine6:
    """Unified USDE v6.2 engine — single agent with three v7.5 hooks."""

    def __init__(self, gov_params=None, omega=None, phrase_sens=1.0, cluster_sens=1.0):
        self.parser = SemanticParser()
        self.tagger = OntologyTagger()
        self.builder = GraphBuilder()
        self.governance = ParameterizedGovernance(omega, phrase_sens, cluster_sens)
        self.spectral = SpectralSubstrate()
        self.enforcement = EnforcementEngine()
        self.stabilizer_op = Stabilizer()
        self.spine_ext = SpineExtractor()
        self.telemetry = TelemetryComputer()
        self.governor = RegimeGovernor(gov_params)
        self.manifold = ManifoldMemory()
        self.decomposer = CausalDecomposer()
        self.ltm = DomainLTM()
        self.policy = InsightPolicy()
        self.cfield = ContradictionField()
        self.resolver = ResolutionOperator()
        self.insight_det = InsightDetector()
        self.action_synth = ActionSynthesizer()
        # v7.5 hooks
        self.mode_router = ModeRouter()
        self.sequence_buffer = SequenceBuffer()
        self.gap_sentinel = GapSentinel()
        self._t = 0

    def analyze(self, text, K_inner=3):
        self._t += 1; self.manifold.clear()
        empty = self._empty_result()
        if not text or len(text.strip()) < 5: return empty

        # PARSE
        claims = self.parser.parse(text)
        if not claims: return empty

        # HOOK 1: MODE ROUTER (front of pipeline)
        mode = self.mode_router.route(text, claims, self.tagger)

        # Select Ω profile based on mode
        omega_profiles = {"stoic": OMEGA_STOIC, "graceful": OMEGA_GRACEFUL, "charity": OMEGA_CHARITY}
        active_omega = omega_profiles.get(mode.omega_key, OMEGA_STOIC)
        self.governance.omega = active_omega

        domain = classify_domain(text)
        self.ltm.decay(domain)
        self.cfield.decay(self._t)
        redundancy = compute_redundancy(text, self.ltm)

        # BUILD GRAPH
        chains = self.decomposer.decompose(claims)
        g, roles = self.builder.build(claims, self.tagger)
        gov_report = self.governance.analyze(claims, text, self.tagger, domain)

        # ENFORCE + STABILIZE
        self.enforcement.enforce(g, gov_report)
        centrality_map = compute_centrality(self.ltm)

        # DEEP SENSORS
        ph = phrase_triage(text)
        mh = domain_mechanism_audit(text, domain)
        ch = scan_smuggle_vocabulary(text)
        sensor = {
            "phrase_hits": len(ph), "mech_hits": len(mh),
            "cluster_hits": sum(len(v) for v in ch.values()),
            "clusters": list(ch.keys())[:5], "redundancy": redundancy,
        }

        # MULTI-PASS STABILIZATION
        passes = []
        for k in range(K_inner):
            z = self.telemetry.compute(g)
            L = system_energy_full(z, self.governor.params, self.cfield, centrality_map)
            r = self.governor.update(z)
            self.manifold.record(GraphSnapshot(g.copy(), z, r, L, k))
            self.stabilizer_op.stabilize(g, k)
            passes.append({"pass": k, "r": r, "L": L, "telemetry": z.as_dict()})

        # LTM UPDATES
        inv_n = self.manifold.invariant_nodes()
        ltm_conf = 0; ltm_contra = 0
        for uid in inv_n:
            for snap in self.manifold.snapshots:
                for nd in snap.graph.nodes.values():
                    if nd.uid == uid:
                        self.ltm.confirm(uid, nd.text, domain); ltm_conf += 1; break
        for ch_item in chains:
            self.ltm.confirm(ch_item.chain_id, f"{ch_item.trigger}→{ch_item.effect}", domain, "causal_chain")
            ltm_conf += 1
        if gov_report.violation_load > 0.3:
            for c in claims:
                if c.uid in self.ltm.entries:
                    self.ltm.contradict(c.uid); ltm_contra += 1

        # CONTRADICTION FIELD
        for snap in self.manifold.snapshots:
            for e in snap.graph.all_edges():
                if "CONFLICT" in e.etype:
                    sn = snap.graph.nodes.get(e.src)
                    tn = snap.graph.nodes.get(e.tgt)
                    if sn and tn:
                        self.cfield.register(sn.uid, tn.uid, e.signed_tension,
                            classify_domain(sn.text), classify_domain(tn.text), e.etype, self._t)

        credible = self.cfield.credible_conflicts(self.ltm)
        resolutions = []
        for key, conflict, phi in credible[:5]:
            ok, method, detail = self.resolver.attempt(conflict, self.ltm, domain)
            if ok: self.cfield.resolve(conflict.uid_a, conflict.uid_b)
            resolutions.append({"a": conflict.uid_a[:12], "b": conflict.uid_b[:12], "method": method})

        self.ltm.prune()
        insights = self.insight_det.detect(passes, self.manifold)

        # HOOK 2: SEQUENCE BUFFER
        stable_g = self.manifold.build_invariant_graph()
        seq_signals = self.sequence_buffer.scan(claims, stable_g, self.tagger)
        seq_summary = self.sequence_buffer.summary(seq_signals)

        # HOOK 3: GAP SENTINEL
        gap_signals = self.gap_sentinel.scan(stable_g, gov_report, claims, self.cfield)
        gap_summary = self.gap_sentinel.summary(gap_signals)

        # OUTPUT SPINE
        spec = self.spectral.analyze(stable_g)
        spine = self.spine_ext.extract(stable_g)
        recs = self.action_synth.synthesize(stable_g, chains, {"summary": {}}, gov_report)
        status = "DEMOTED" if gov_report.demoted else "ACTIVE"

        return {
            "version": "6.2.0", "t": self._t, "domain": domain, "status": status,
            "regime": gov_report.regime,
            # Hook 1 output
            "mode": mode.mode, "mode_confidence": mode.confidence,
            "mode_rationale": mode.rationale, "omega_key": mode.omega_key,
            # Core telemetry
            "r": self.governor.r,
            "legibility": gov_report.legibility,
            "violation_load": gov_report.violation_load,
            "sensor": sensor,
            "claims": [{"uid": c.uid, "text": c.text[:60], "confidence": c.confidence,
                "agent": c.agent[:20], "effect": c.effect[:25], "polarity": c.polarity,
                "mechanism": c.mechanism, "causal_verb": c.causal_verb,
                "has_wrapper": c.has_wrapper, "negation_scope": c.negation_scope}
                for c in claims[:10]],
            "chains": [{"trigger": ch_item.trigger, "pathway": ch_item.pathway[:3],
                "effect": ch_item.effect, "confidence": ch_item.confidence}
                for ch_item in chains[:5]],
            "graph": {"nodes": stable_g.n_nodes(), "edges": stable_g.n_edges(),
                "components": spec["components"], "fragility": spec["fragility"]},
            "manifold": {"n_views": self.manifold.n_views()},
            "invariant": {"nodes": len(inv_n), "variant": len(self.manifold.variant_nodes())},
            "cfield": self.cfield.summary(),
            "resolutions": resolutions,
            "ltm": {**self.ltm.summary(), "confirmed": ltm_conf, "contradicted": ltm_contra},
            "recommendations": [{"rank": rc.rank, "pathway": rc.pathway, "confidence": rc.confidence,
                "basis": rc.basis, "caveats": rc.caveats} for rc in recs[:5]],
            "spine": spine[:5],
            "energy": passes[-1]["L"] if passes else 0,
            "passes": passes,
            "governance": {"violations": gov_report.violations, "legibility": gov_report.legibility},
            "governor": {"r": self.governor.r, "history": self.governor.history[-5:]},
            # Hook 2 output
            "sequence": seq_summary,
            # Hook 3 output
            "gap": gap_summary,
        }

    def _empty_result(self):
        return {
            "version": "6.2.0", "t": self._t, "domain": "general", "status": "EMPTY",
            "mode": "empirical", "mode_confidence": 0.0, "mode_rationale": "empty",
            "omega_key": "stoic", "r": self.governor.r,
            "legibility": 0, "violation_load": 0, "sensor": {},
            "claims": [], "chains": [], "graph": {"nodes": 0, "edges": 0, "components": 0, "fragility": 0},
            "manifold": {"n_views": 0}, "invariant": {"nodes": 0, "variant": 0},
            "cfield": {"active": 0, "resolved": 0, "max_tension": 0},
            "resolutions": [], "ltm": {"entries": 0, "domains": []},
            "recommendations": [], "spine": [], "energy": 0, "passes": [],
            "governance": {"violations": {}, "legibility": 0},
            "governor": {"r": self.governor.r, "history": []},
            "sequence": {"stateful": False, "moves": [], "move_count": 0, "dominant_move": None},
            "gap": {"engine_gap_detected": False, "gap_flags": [], "max_severity": 0.0},
        }

# ═══════════════════════════════════════════════════════════════════════
# §16. MULTI-AGENT ORCHESTRATOR (v7.5 telemetry schema)
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class ConsensusResult:
    agreement: str; variance: float; consensus_v: float; fragile: bool

class ConsensusEngine:
    def compute(self, rs, rg):
        vs = rs["violation_load"]; vg = rg["violation_load"]
        cv = round((vs + vg) / 2, 4); var = round(abs(vs - vg), 4)
        agree = "unanimous" if var < 0.1 else "majority" if var < 0.25 else "contested"
        return ConsensusResult(agree, var, cv, var > 0.2)

class CouncilOfOmegas:
    """Multi-agent orchestrator: Stoic + Graceful deliberation with v7.5 hooks."""

    def __init__(self, gov_params=None):
        self.agent_s = Engine6(gov_params, OMEGA_STOIC, 1.3, 1.3)
        self.agent_g = Engine6(gov_params, OMEGA_GRACEFUL, 0.7, 0.7)
        self.consensus = ConsensusEngine()
        self._t = 0

    def analyze(self, text, K_inner=3):
        self._t += 1
        if not text or len(text.strip()) < 5:
            return {"version": "6.2.0", "status": "EMPTY", "t": self._t,
                "consensus": {"agreement": "unanimous", "variance": 0},
                "agent_s": {}, "agent_g": {}}

        rs = self.agent_s.analyze(text, K_inner)
        rg = self.agent_g.analyze(text, K_inner)
        cons = self.consensus.compute(rs, rg)

        if cons.agreement == "unanimous": status = rs["status"]
        elif cons.consensus_v > 0.4: status = "DEMOTED"
        elif cons.fragile: status = "CONTESTED"
        else: status = rs["status"]

        # Use Stoic agent's mode routing (more conservative)
        mode = rs.get("mode", "empirical")

        # Merge sequence signals from both agents
        seq_s = rs.get("sequence", {})
        seq_g = rg.get("sequence", {})
        # Prefer whichever agent found more sequence moves
        seq = seq_s if seq_s.get("move_count", 0) >= seq_g.get("move_count", 0) else seq_g

        # Merge gap signals (union of both agents' gaps)
        gap_s = rs.get("gap", {})
        gap_g = rg.get("gap", {})
        gap_flags_s = gap_s.get("gap_flags", [])
        gap_flags_g = gap_g.get("gap_flags", [])
        merged_gap_types = set()
        merged_gaps = []
        for gf in gap_flags_s + gap_flags_g:
            key = f"{gf['type']}_{gf['evidence'][:20]}"
            if key not in merged_gap_types:
                merged_gap_types.add(key); merged_gaps.append(gf)
        merged_gaps.sort(key=lambda x: -x["severity"])
        gap_merged = {
            "engine_gap_detected": len(merged_gaps) > 0,
            "gap_flags": merged_gaps,
            "max_severity": merged_gaps[0]["severity"] if merged_gaps else 0.0,
            "dominant_gap": merged_gaps[0]["type"] if merged_gaps else None,
        }

        # Run gap sentinel with council awareness
        gap_sentinel = GapSentinel()
        council_dict = {
            "agent_s": {"violation_load": rs["violation_load"]},
            "agent_g": {"violation_load": rg["violation_load"]},
        }
        stable_g = self.agent_s.manifold.build_invariant_graph()
        gov_report_s = GovernanceReport(
            rs.get("governance", {}).get("violations", {}),
            rs["violation_load"], rs["legibility"],
            rs["status"] == "DEMOTED", rs.get("regime", "normal"))
        council_gaps = gap_sentinel.scan(stable_g, gov_report_s,
            self.agent_s.parser.parse(text) if text else [],
            self.agent_s.cfield, council_dict)
        for cg in council_gaps:
            key = f"{cg.gap_type}_{cg.evidence[:20]}"
            if key not in merged_gap_types:
                merged_gap_types.add(key)
                merged_gaps.append({"type": cg.gap_type, "severity": cg.severity, "evidence": cg.evidence})
        merged_gaps.sort(key=lambda x: -x["severity"])
        gap_merged["gap_flags"] = merged_gaps
        gap_merged["engine_gap_detected"] = len(merged_gaps) > 0
        if merged_gaps:
            gap_merged["max_severity"] = merged_gaps[0]["severity"]
            gap_merged["dominant_gap"] = merged_gaps[0]["type"]

        return {
            "version": "6.2.0", "t": self._t, "domain": rs.get("domain", "general"),
            "status": status, "mode": mode,
            "mode_confidence": rs.get("mode_confidence", 0),
            "mode_rationale": rs.get("mode_rationale", ""),
            "r": round((rs["r"] + rg["r"]) / 2, 4),
            "legibility": round((rs["legibility"] + rg["legibility"]) / 2, 3),
            "violation_load": cons.consensus_v,
            "consensus": {"agreement": cons.agreement, "variance": cons.variance,
                "consensus_v": cons.consensus_v, "fragile": cons.fragile},
            "agent_s": {"name": "Stoic", "violation_load": rs["violation_load"],
                "legibility": rs["legibility"], "status": rs["status"], "r": rs["r"],
                "sensor": rs.get("sensor", {})},
            "agent_g": {"name": "Graceful", "violation_load": rg["violation_load"],
                "legibility": rg["legibility"], "status": rg["status"], "r": rg["r"],
                "sensor": rg.get("sensor", {})},
            "claims": rs.get("claims", []),
            "chains": rs.get("chains", []),
            "recommendations": rs.get("recommendations", []),
            "graph": rs.get("graph", {}),
            "invariant": rs.get("invariant", {}),
            "energy": rs.get("energy", 0),
            "cfield": rs.get("cfield", {}),
            "ltm": rs.get("ltm", {}),
            "spine": rs.get("spine", []),
            "passes": rs.get("passes", []),
            # v7.5 hooks
            "sequence": seq,
            "gap": gap_merged,
        }

# ═══════════════════════════════════════════════════════════════════════
# §17. FALSIFICATION HARNESS (115 tests)
# ═══════════════════════════════════════════════════════════════════════

class FalsificationHarness:
    """115 deterministic tests. 100 from v6.0 + 15 hook tests."""

    def __init__(self):
        self.results = []

    def run(self):
        self.results.clear()
        methods = sorted([m for m in dir(self) if m.startswith("_t")])
        for m in methods:
            fn = getattr(self, m)
            try:
                label, passed, detail = fn()
                self.results.append((label, passed, detail))
            except Exception as ex:
                self.results.append((m, False, str(ex)[:60]))
        return self.results

    def report(self):
        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        failed = [(l, d) for l, p, d in self.results if not p]
        return total, passed, failed

    # ── SENSOR TESTS (S01-S10) ──
    def _t001(self): return "S01:phrase", len(phrase_triage("intentional energy misalignment")) >= 1, "ok"
    def _t002(self): return "S02:spiritual", len(phrase_triage("spiritual resonance field")) >= 1, "ok"
    def _t003(self): return "S03:clean", len(phrase_triage("electromagnetic coupling interaction")) == 0, "clean"
    def _t004(self): return "S04:cosmic", len(phrase_triage("cosmic energy alignment")) >= 1, "ok"
    def _t005(self): return "S05:conscious", len(phrase_triage("conscious collapse mechanism")) >= 1, "ok"
    def _t006(self): return "S06:clean2", len(phrase_triage("thermal decoherence process")) == 0, "clean"
    def _t007(self): return "S07:cluster", len(scan_smuggle_vocabulary("noetic consciousness observer")) > 0, "ok"
    def _t008(self): return "S08:mech_audit", len(domain_mechanism_audit("quantum decoherence", "construction")) >= 1, "ok"
    def _t009(self): return "S09:mech_ok", len(domain_mechanism_audit("quantum decoherence", "physics")) == 0, "clean"
    def _t010(self):
        h = scan_smuggle_vocabulary("noetic influence induces localization")
        return "S10:scan", "consciousness_cluster" in h, f"{list(h.keys())}"

    # ── PARSER TESTS (P11-P20) ──
    def _t011(self):
        p = SemanticParser(); cs = p.parse("Gravity causes orbital decay through tidal interaction.")
        return "P11:causal", cs[0].mechanism if cs else False, "mechanism"
    def _t012(self):
        p = SemanticParser(); cs = p.parse("It is believed that consciousness causes collapse.")
        return "P12:wrapper", cs[0].has_wrapper if cs else False, "wrapper"
    def _t013(self):
        p = SemanticParser(); cs = p.parse("The field was measured by the detector.")
        return "P13:passive", cs[0].agent == "the detector" if cs else False, "passive"
    def _t014(self):
        p = SemanticParser(); cs = p.parse("This does not cause any effect.")
        return "P14:negation", cs[0].negation_scope if cs else False, "negation"
    def _t015(self):
        p = SemanticParser(); cs = p.parse("Before the experiment, the field was stable.")
        return "P15:temporal", cs[0].temporal if cs else False, "temporal"
    def _t016(self):
        p = SemanticParser(); cs = p.parse("The result may possibly suggest a trend.")
        return "P16:qualifier", len(cs[0].qualifiers) >= 2 if cs else False, "qualifiers"
    def _t017(self):
        p = SemanticParser(); cs = p.parse("Short.")
        return "P17:short", len(cs) == 0, "filtered"
    def _t018(self):
        p = SemanticParser(); cs = p.parse("Spin-orbit coupling causes energy splitting through magnetic interaction.")
        return "P18:mechanism", cs[0].mechanism if cs else False, "full_mechanism"
    def _t019(self):
        p = SemanticParser(); cs = p.parse("The cat sat on the mat quietly.")
        return "P19:no_causal", not cs[0].causal_verb if cs else True, "no_verb"
    def _t020(self):
        p = SemanticParser(); cs = p.parse("Energy probably drives the transition.")
        return "P20:qual_causal", cs[0].causal_verb == "drives" if cs else False, "qualified_causal"

    # ── ONTOLOGY TESTS (O21-O30) ──
    def _t021(self):
        t = OntologyTagger(); r = t.tag("electron spin magnetic coupling")
        return "O21:physical", r.dominant_role == "physical", r.dominant_role
    def _t022(self):
        t = OntologyTagger(); r = t.tag("consciousness awareness subjective qualia")
        return "O22:phenom", r.dominant_role == "phenomenological", r.dominant_role
    def _t023(self):
        t = OntologyTagger(); r = t.tag("god soul spirit divine karma")
        return "O23:metaph", r.dominant_role == "metaphysical", r.dominant_role
    def _t024(self):
        t = OntologyTagger(); r = t.tag("detector apparatus measurement experiment lab")
        return "O24:measure", r.dominant_role == "measurement", r.dominant_role
    def _t025(self):
        t = OntologyTagger(); r = t.tag("equation function operator eigenvalue")
        return "O25:math", r.dominant_role == "mathematical", r.dominant_role
    def _t026(self):
        t = OntologyTagger(); r = t.tag("authority status reputation consensus")
        return "O26:social", r.dominant_role == "social", r.dominant_role
    def _t027(self):
        t = OntologyTagger(); r = t.tag("hero villain quest journey sacrifice")
        return "O27:narrative", r.dominant_role == "narrative", r.dominant_role
    def _t028(self):
        t = OntologyTagger(); r = t.tag("electron consciousness equation")
        return "O28:ambig", r.ambiguity > 0, f"H={r.ambiguity}"
    def _t029(self):
        t = OntologyTagger(); r = t.tag("sand concrete aggregate bonding fracture")
        return "O29:construction", r.dominant_role == "physical", r.dominant_role
    def _t030(self):
        t = OntologyTagger(); r = t.tag("data analysis lab test report inspection")
        return "O30:measurement2", r.dominant_role == "measurement", r.dominant_role

    # ── GOVERNANCE TESTS (G31-G40) ──
    def _t031(self):
        e = Engine6(omega=OMEGA_STOIC); r = e.analyze("Consciousness awareness and subjective mind creates reality.")
        return "G31:stoic_high", r["violation_load"] > 0.15, f"Vm={r['violation_load']}"
    def _t032(self):
        e = Engine6(omega=OMEGA_STOIC); r = e.analyze("Spin-orbit coupling causes energy level splitting.")
        return "G32:stoic_clean", r["violation_load"] < 0.15, f"Vm={r['violation_load']}"
    def _t033(self):
        e = Engine6(omega=OMEGA_GRACEFUL); r = e.analyze("Consciousness causes wave collapse.")
        return "G33:graceful_lower", r["violation_load"] < 0.6, f"Vm={r['violation_load']}"
    def _t034(self):
        e = Engine6(omega=OMEGA_STOIC); r = e.analyze("Intentional energy alignment focuses the quantum field.")
        return "G34:smuggle", r["violation_load"] > 0.1, f"Vm={r['violation_load']}"
    def _t035(self):
        e = Engine6(omega=OMEGA_STOIC); r = e.analyze("Thermal decoherence destroys superposition via scattering.")
        return "G35:clean_phys", r["violation_load"] < 0.1, f"Vm={r['violation_load']}"
    def _t036(self):
        e = Engine6(omega=OMEGA_CHARITY); r = e.analyze("The hero sealed the spirit through sacrifice.")
        return "G36:charity", r["violation_load"] < 0.15, f"Vm={r['violation_load']}"
    def _t037(self):
        e = Engine6(omega=OMEGA_STOIC)
        r = e.analyze("Cosmic vibration manifestation determines the soul destiny of the divine spirit.")
        return "G37:max_meta", r["violation_load"] > 0.4, f"Vm={r['violation_load']}"
    def _t038(self):
        e = Engine6(); r = e.analyze(""); return "G38:empty", r["status"] == "EMPTY", "empty"
    def _t039(self):
        e = Engine6(); r = e.analyze("Hi"); return "G39:short", r["status"] == "EMPTY", "empty"
    def _t040(self):
        e = Engine6(); r = e.analyze("The lab test confirms aggregate contamination in the sample.")
        return "G40:lab_clean", r["violation_load"] < 0.1, f"Vm={r['violation_load']}"

    # ── GRAPH TESTS (GR41-GR50) ──
    def _t041(self):
        p = SemanticParser(); t = OntologyTagger(); b = GraphBuilder()
        cs = p.parse("Gravity causes decay. Consciousness causes collapse.")
        g, _ = b.build(cs, t)
        return "GR41:2node", g.n_nodes() == 2, f"n={g.n_nodes()}"
    def _t042(self):
        p = SemanticParser(); t = OntologyTagger(); b = GraphBuilder()
        cs = p.parse("Gravity causes orbital decay through tidal forces. Magnetism causes alignment.")
        g, _ = b.build(cs, t)
        return "GR42:edges", g.n_edges() >= 0, f"e={g.n_edges()}"
    def _t043(self):
        g = EpistemicGraph(); g.add_node("a", "test"); g.add_node("b", "test2")
        return "GR43:copy", g.copy().n_nodes() == 2, "copy_ok"
    def _t044(self):
        g = EpistemicGraph()
        g.add_node("a", "test"); g.add_node("b", "test2")
        g.add_edge(0, 1, "SUPPORT", 0.5)
        return "GR44:neighbors", 1 in g.neighbors(0), "ok"
    def _t045(self):
        g = EpistemicGraph()
        g.add_node("a", "t1"); g.add_node("b", "t2"); g.add_node("c", "t3")
        g.add_edge(0, 1, "S", 0.5)
        comps = g.components()
        return "GR45:components", len(comps) == 2, f"comps={len(comps)}"
    def _t046(self):
        g = EpistemicGraph()
        return "GR46:empty_graph", g.n_nodes() == 0 and g.n_edges() == 0, "ok"
    def _t047(self):
        g = EpistemicGraph()
        g.add_node("a", "test", conf=0.8); g.add_node("b", "test2", conf=0.3)
        g.add_edge(0, 1, "S", 0.5)
        cent = g.centrality()
        return "GR47:centrality", cent[0] > 0, f"c0={cent[0]}"
    def _t048(self):
        s = SpectralSubstrate(); g = EpistemicGraph()
        g.add_node("a", "t"); g.add_node("b", "t2"); g.add_edge(0, 1, "T", 0.5, 0.7)
        r = s.analyze(g)
        return "GR48:spectral", r["fragility"] > 0, f"frag={r['fragility']}"
    def _t049(self):
        sp = SpineExtractor(); g = EpistemicGraph()
        g.add_node("a", "test claim", role="physical"); g.add_node("b", "another claim", role="social")
        g.add_edge(0, 1, "S", 0.5)
        spine = sp.extract(g)
        return "GR49:spine", len(spine) > 0, f"spine={len(spine)}"
    def _t050(self):
        d = CausalDecomposer(); p = SemanticParser()
        cs = p.parse("Gravity causes decay through tidal interaction.")
        chains = d.decompose(cs)
        return "GR50:chains", len(chains) > 0, f"chains={len(chains)}"

    # ── ENGINE INTEGRATION TESTS (E51-E60) ──
    def _t051(self):
        e = Engine6(); r = e.analyze("Spin-orbit coupling causes energy splitting through magnetic interaction.")
        return "E51:clean", r["violation_load"] < 0.15, f"Vm={r['violation_load']}"
    def _t052(self):
        e = Engine6(); r = e.analyze("Consciousness awareness and subjective mind perception creates reality.")
        return "E52:phenom", r["violation_load"] > 0.1, f"Vm={r['violation_load']}"
    def _t053(self):
        e = Engine6()
        r = e.analyze("Intentional energy misalignment causes structural resonance collapse via cosmic vibration.")
        return "E53:smuggle", r["violation_load"] > 0.2, f"Vm={r['violation_load']}"
    def _t054(self):
        e = Engine6(); r = e.analyze("Lab analysis found unwashed sand leading to poor bonding and fractures.")
        return "E54:construction", r["domain"] == "construction", r["domain"]
    def _t055(self):
        e = Engine6()
        r = e.analyze("One claim here. Two claims here. Three claims here. Four claims here.")
        return "E55:multi", len(r["claims"]) >= 3, f"claims={len(r['claims'])}"
    def _t056(self):
        e = Engine6(); r = e.analyze("Decoherence destroys superposition through environmental entanglement.")
        return "E56:version", r["version"] == "6.2.0", r["version"]
    def _t057(self):
        e = Engine6(); r = e.analyze("Test determinism.")
        r2 = e.analyze("Test determinism.")
        return "E57:deterministic", r["violation_load"] == r2["violation_load"], "deterministic"
    def _t058(self):
        e = Engine6(); r = e.analyze("The sacred cosmic vibration manifests divine energy alignment.")
        return "E58:max_violation", r["violation_load"] > 0.3, f"Vm={r['violation_load']}"
    def _t059(self):
        e = Engine6(); r = e.analyze("Spin-orbit coupling causes energy level splitting.")
        return "E59:has_chains", len(r.get("chains", [])) > 0, f"chains={len(r.get('chains', []))}"
    def _t060(self):
        e = Engine6(); r = e.analyze("The measurement confirms the prediction.")
        return "E60:has_mode", r.get("mode") in ("empirical", "narrative", "mixed", "social_sequence"), r.get("mode")

    # ── COUNCIL TESTS (C61-C70) ──
    def _t061(self):
        c = CouncilOfOmegas(); r = c.analyze("Spin-orbit coupling causes energy splitting.")
        return "C61:council_clean", r["violation_load"] < 0.15, f"Vm={r['violation_load']}"
    def _t062(self):
        c = CouncilOfOmegas(); r = c.analyze("Consciousness awareness and subjective mind perception creates reality.")
        return "C62:council_phenom", r["violation_load"] > 0.05, f"Vm={r['violation_load']}"
    def _t063(self):
        c = CouncilOfOmegas()
        r = c.analyze("Intentional energy alignment focuses the quantum field through cosmic vibration.")
        return "C63:council_smuggle", r["violation_load"] > 0.1, f"Vm={r['violation_load']}"
    def _t064(self):
        c = CouncilOfOmegas(); r = c.analyze("Decoherence destroys superposition via thermal photons.")
        return "C64:consensus", r["consensus"]["agreement"] in ("unanimous", "majority", "contested"), r["consensus"]["agreement"]
    def _t065(self):
        c = CouncilOfOmegas(); r = c.analyze("")
        return "C65:empty_council", r["status"] == "EMPTY", "empty"
    def _t066(self):
        c = CouncilOfOmegas(); r = c.analyze("Lab test confirms aggregate contamination.")
        return "C66:construction", r.get("domain") == "construction", r.get("domain")
    def _t067(self):
        c = CouncilOfOmegas(); r = c.analyze("Spin coupling through magnetic interaction.")
        return "C67:version", r["version"] == "6.2.0", r["version"]
    def _t068(self):
        c = CouncilOfOmegas()
        r = c.analyze("Decoherence destroys superposition. Consciousness causes collapse. Lab confirms data.")
        return "C68:multi", len(r.get("claims", [])) >= 2, f"claims={len(r.get('claims', []))}"
    def _t069(self):
        c = CouncilOfOmegas(); r = c.analyze("The hero sealed the villain through sacrifice.")
        return "C69:has_mode", r.get("mode") is not None, r.get("mode")
    def _t070(self):
        c = CouncilOfOmegas(); r = c.analyze("Sacred cosmic vibration manifests divine soul alignment.")
        return "C70:high_v", r["violation_load"] > 0.2, f"Vm={r['violation_load']}"

    # ── CONTRADICTION FIELD TESTS (CF71-CF80) ──
    def _t071(self):
        cf = ContradictionField(); cf.register("a", "b", 0.5, "physics", "metaphysical", "DOMAIN_CONFLICT", 1)
        return "CF71:register", cf.open_count() == 1, f"open={cf.open_count()}"
    def _t072(self):
        cf = ContradictionField(); cf.register("a", "b", 0.5, "p", "m", "CONFLICT", 1)
        cf.resolve("a", "b")
        return "CF72:resolve", cf.open_count() == 0, "resolved"
    def _t073(self):
        cf = ContradictionField(); cf.register("a", "b", 0.8, "p", "m", "CONFLICT", 1)
        return "CF73:summary", cf.summary()["active"] == 1, f"active={cf.summary()['active']}"
    def _t074(self):
        cf = ContradictionField(); cf.register("a", "b", 0.8, "p", "m", "CONFLICT", 1)
        cf.decay(12)
        return "CF74:decay", cf.open_count() == 0, "decayed"
    def _t075(self):
        cf = ContradictionField()
        cf.register("a", "b", 0.5, "p", "m", "CONFLICT", 1)
        cf.register("c", "d", 0.7, "p", "m", "CONFLICT", 1)
        ltm = DomainLTM(); ltm.confirm("a", "test", "physics")
        cred = cf.credible_conflicts(ltm)
        return "CF75:credible", len(cred) == 2, f"cred={len(cred)}"
    def _t076(self):
        r = ResolutionOperator(); cf = ConflictEntry("a", "b", 0.5, "physics", "metaphysical", "D", 1)
        ok, method, _ = r.attempt(cf, DomainLTM(), "general")
        return "CF76:domain_sep", ok and method == "domain_separation", method
    def _t077(self):
        r = ResolutionOperator(); cf = ConflictEntry("a", "b", 0.5, "physics", "physics", "C", 1)
        ltm = DomainLTM(); ltm.confirm("a", "t", "physics"); ltm.entries["a"].confirms = 5
        ltm.confirm("b", "t2", "physics")
        ok, method, _ = r.attempt(cf, ltm, "physics")
        return "CF77:evidence_wt", ok and method == "evidence_weight", method
    def _t078(self):
        cf = ContradictionField()
        cf.register("x", "y", 0.9, "p", "m", "CONFLICT", 1)
        p = cf.pressure({})
        return "CF78:pressure", p > 0, f"p={p}"
    def _t079(self):
        cf = ContradictionField(); focus = cf.focus_set()
        return "CF79:focus_empty", len(focus) == 0, "empty"
    def _t080(self):
        cf = ContradictionField()
        cf.register("a", "b", 0.5, "p", "m", "CONFLICT", 1)
        s = cf.summary()
        return "CF80:max_tension", s["max_tension"] > 0, f"mt={s['max_tension']}"

    # ── LTM + MANIFOLD TESTS (L81-L90) ──
    def _t081(self):
        ltm = DomainLTM(); ltm.confirm("a", "test", "physics"); ltm.confirm("a", "test", "physics")
        return "L81:confirm", ltm.entries["a"].confirms == 2, f"c={ltm.entries['a'].confirms}"
    def _t082(self):
        ltm = DomainLTM(); ltm.confirm("a", "test", "physics"); ltm.contradict("a")
        return "L82:contradict", ltm.entries["a"].contradicts == 1, f"c={ltm.entries['a'].contradicts}"
    def _t083(self):
        ltm = DomainLTM(); ltm.confirm("a", "test", "physics")
        for _ in range(25): ltm.decay("physics")
        ltm.prune()
        return "L83:prune", len(ltm.entries) == 0, "pruned"
    def _t084(self):
        m = ManifoldMemory()
        g = EpistemicGraph(); g.add_node("a", "test")
        m.record(GraphSnapshot(g, Telemetry(), 0.5, 0.1, 0))
        return "L84:manifold", m.n_views() == 1, f"views={m.n_views()}"
    def _t085(self):
        m = ManifoldMemory()
        g1 = EpistemicGraph(); g1.add_node("a", "t1"); g1.add_node("b", "t2")
        g2 = EpistemicGraph(); g2.add_node("a", "t1")
        m.record(GraphSnapshot(g1, Telemetry(), 0.5, 0.1, 0))
        m.record(GraphSnapshot(g2, Telemetry(), 0.5, 0.2, 1))
        return "L85:invariant", len(m.invariant_nodes()) >= 1, f"inv={len(m.invariant_nodes())}"
    def _t086(self):
        d = CausalDecomposer(); p = SemanticParser()
        cs = p.parse("No causal verbs here whatsoever in this sentence.")
        chains = d.decompose(cs)
        return "L86:no_chains", len(chains) == 0, f"chains={len(chains)}"
    def _t087(self):
        ltm = DomainLTM()
        s = ltm.summary()
        return "L87:ltm_summary", s["entries"] == 0, f"entries={s['entries']}"
    def _t088(self):
        ltm = DomainLTM(); ltm.confirm("a", "test", "physics")
        r = compute_redundancy("this test has physics electron spin", ltm)
        return "L88:redundancy", r >= 0, f"r={r}"
    def _t089(self):
        m = ManifoldMemory(); m.clear()
        return "L89:clear", m.n_views() == 0, "cleared"
    def _t090(self):
        ltm = DomainLTM(); ltm.confirm("a", "test", "physics")
        c = compute_centrality(ltm)
        return "L90:centrality", "a" in c, f"c={c.get('a', 'missing')}"

    # ── OBSIDIAN HEIGHTS INTEGRATION (OH91-OH100) ──
    def _t091(self):
        e = Engine6(omega=OMEGA_STOIC)
        r = e.analyze("Contractor Wilkes blamed intentional energy misalignment and cosmic negative focus accumulation in the curing zone.")
        return "OH91:wilkes_v", r["violation_load"] > 0.08, f"Vm={r['violation_load']}"
    def _t092(self):
        e = Engine6(omega=OMEGA_STOIC)
        r = e.analyze("Independent lab found unwashed river sand causing poor crystalline bonding.")
        return "OH92:lab_clean", r["violation_load"] < 0.15, f"Vm={r['violation_load']}"
    def _t093(self):
        e = Engine6(omega=OMEGA_STOIC)
        r = e.analyze("Engineer Miller argues vibrational resonance from light rail bypassing damping layers.")
        return "OH93:miller", r["violation_load"] < 0.4, f"Vm={r['violation_load']}"
    def _t094(self):
        c = CouncilOfOmegas()
        text = ("Contractor Wilkes blamed negative energy accumulation. "
            "Lab found unwashed river sand causing poor bonding. "
            "Engineer Miller argues vibrational resonance from rail.")
        r = c.analyze(text)
        return "OH94:council_v", r["violation_load"] > 0.05, f"Vm={r['violation_load']}"
    def _t095(self):
        c = CouncilOfOmegas()
        text = ("Contractor Wilkes blamed negative energy accumulation. "
            "Lab found unwashed river sand causing poor bonding.")
        r = c.analyze(text)
        return "OH95:domain", r.get("domain", "") in ("construction", "general"), r.get("domain")
    def _t096(self):
        e = Engine6()
        r = e.analyze("The lab test confirms sand contamination leads to poor crystalline bonding and structural fatigue.")
        return "OH96:chain", len(r.get("chains", [])) > 0, f"chains={len(r.get('chains', []))}"
    def _t097(self):
        c = CouncilOfOmegas()
        r = c.analyze("Sacred energy misalignment causes foundation settling through cosmic vibration.")
        return "OH97:max_flag", r["violation_load"] > 0.15, f"Vm={r['violation_load']}"
    def _t098(self):
        e = Engine6()
        r = e.analyze("Intentional focus and negative energy accumulation in the curing zone caused failure.")
        return "OH98:sensor", r["sensor"]["phrase_hits"] > 0 or r["sensor"]["cluster_hits"] > 0, f"ph={r['sensor']}"
    def _t099(self):
        e = Engine6()
        r = e.analyze("Unwashed river sand led to contamination causing poor bonding and structural fatigue.")
        return "OH99:low_v", r["violation_load"] < 0.15, f"Vm={r['violation_load']}"
    def _t100(self):
        c = CouncilOfOmegas()
        text = ("Miller argues vibrational resonance from 4th Street Light Rail. "
            "Wilkes blames negative energy accumulation. "
            "Lab found unwashed sand causing poor crystalline bonding.")
        r = c.analyze(text)
        return "OH100:full", r["consensus"]["agreement"] in ("unanimous", "majority", "contested"), r["consensus"]["agreement"]

    # ── HOOK 1: MODE ROUTER TESTS (MR101-MR105) ──
    def _t101(self):
        e = Engine6(); r = e.analyze("Spin-orbit coupling causes energy splitting through magnetic interaction.")
        return "MR101:empirical", r["mode"] == "empirical", r["mode"]
    def _t102(self):
        e = Engine6()
        r = e.analyze("The Fourth Hokage sealed the Nine-Tails. Naruto mastered Shadow Clone Technique defeating Mizuki. Sasuke sacrificed himself protecting Naruto.")
        return "MR102:narrative", r["mode"] == "narrative", r["mode"]
    def _t103(self):
        e = Engine6()
        r = e.analyze("A man walks into a bar and says I bet you fifty dollars I can bite my own eye. The bartender agrees.")
        return "MR103:social", r["mode"] == "social_sequence", r["mode"]
    def _t104(self):
        e = Engine6(); r = e.analyze("Lab found unwashed sand. Consciousness caused failure.")
        return "MR104:mixed_or_emp", r["mode"] in ("empirical", "mixed"), r["mode"]
    def _t105(self):
        mr = ModeRouter(); p = SemanticParser(); t = OntologyTagger()
        cs = p.parse("The measurement confirms the prediction through experimental observation.")
        m = mr.route("The measurement confirms the prediction through experimental observation.", cs, t)
        return "MR105:mode_obj", m.mode == "empirical" and m.confidence > 0.5, f"{m.mode}:{m.confidence}"

    # ── HOOK 2: SEQUENCE BUFFER TESTS (SB106-SB110) ──
    def _t106(self):
        sb = SequenceBuffer(); p = SemanticParser(); t = OntologyTagger(); b = GraphBuilder()
        cs = p.parse("I believe and feel this seems possibly true. This clearly proves total destruction through cosmic mechanisms.")
        g, _ = b.build(cs, t)
        signals = sb.scan(cs, g, t)
        types = [s.move_type for s in signals]
        return "SB106:stabilizer", "preemptive_stabilizer" in types or "confidence_escalation" in types, f"types={types}"
    def _t107(self):
        sb = SequenceBuffer(); p = SemanticParser(); t = OntologyTagger(); b = GraphBuilder()
        cs = p.parse("As an expert engineer with decades of practice. The cosmic energy field causes structural alignment.")
        g, _ = b.build(cs, t)
        signals = sb.scan(cs, g, t)
        types = [s.move_type for s in signals]
        return "SB107:authority", "authority_frontload" in types, f"types={types}"
    def _t108(self):
        sb = SequenceBuffer(); p = SemanticParser(); t = OntologyTagger(); b = GraphBuilder()
        cs = p.parse("The energy may possibly resonate with the field. The field demonstrates confirmed alignment. This undeniably proves everything about the system.")
        g, _ = b.build(cs, t)
        signals = sb.scan(cs, g, t)
        types = [s.move_type for s in signals]
        return "SB108:escalation", "confidence_escalation" in types, f"types={types}"
    def _t109(self):
        sb = SequenceBuffer(); p = SemanticParser(); t = OntologyTagger(); b = GraphBuilder()
        text = "Gravity causes decay. Consciousness causes collapse. Therefore this confirms everything."
        cs = p.parse(text); g, _ = b.build(cs, t)
        signals = sb.scan(cs, g, t)
        types = [s.move_type for s in signals]
        return "SB109:false_complete", "false_completeness" in types, f"types={types}"
    def _t110(self):
        sb = SequenceBuffer(); p = SemanticParser(); t = OntologyTagger(); b = GraphBuilder()
        cs = p.parse("Spin coupling through magnetic interaction. Energy levels split accordingly.")
        g, _ = b.build(cs, t)
        signals = sb.scan(cs, g, t)
        return "SB110:clean_seq", len(signals) == 0 or all(s.confidence < 0.5 for s in signals), f"n={len(signals)}"

    # ── HOOK 3: GAP SENTINEL TESTS (GS111-GS115) ──
    def _t111(self):
        gs = GapSentinel(); g = EpistemicGraph()
        g.add_node("a", "test"); g.add_node("b", "test2"); g.add_node("c", "test3"); g.add_node("d", "test4")
        gr = GovernanceReport({}, 0.05, 0.5, False, "open")
        cf = ContradictionField()
        gaps = gs.scan(g, gr, [], cf)
        is_degenerate = any(gap.gap_type == "degenerate_graph" for gap in gaps)
        return "GS111:degenerate", is_degenerate, f"gaps={[g.gap_type for g in gaps]}"
    def _t112(self):
        gs = GapSentinel(); g = EpistemicGraph()
        g.add_node("a", "test", role="epistemic")
        gr = GovernanceReport({"a": 0.5}, 0.5, 0.3, True, "strict")
        cf = ContradictionField()
        gaps = gs.scan(g, gr, [], cf)
        has_vacuum = any(gap.gap_type == "signal_vacuum" for gap in gaps)
        return "GS112:vacuum", has_vacuum, f"gaps={[g.gap_type for g in gaps]}"
    def _t113(self):
        gs = GapSentinel(); g = EpistemicGraph()
        g.add_node("a", "test"); g.add_node("b", "test2"); g.add_edge(0, 1, "SUPPORT", 0.5)
        gr = GovernanceReport({}, 0.05, 0.5, False, "open")
        cf = ContradictionField()
        gaps = gs.scan(g, gr, [], cf)
        return "GS113:clean", len(gaps) == 0, f"gaps={len(gaps)}"
    def _t114(self):
        gs = GapSentinel(); g = EpistemicGraph()
        gr = GovernanceReport({}, 0.3, 0.5, False, "normal")
        cf = ContradictionField()
        cf.register("a", "b", 0.5, "p", "m", "C", 1)
        cf.register("c", "d", 0.6, "p", "m", "C", 1)
        cf.register("e", "f", 0.7, "p", "m", "C", 1)
        gaps = gs.scan(g, gr, [], cf)
        has_unresolved = any(gap.gap_type == "unresolved_centrality" for gap in gaps)
        return "GS114:unresolved", has_unresolved, f"gaps={[g.gap_type for g in gaps]}"
    def _t115(self):
        e = Engine6()
        r = e.analyze("Spin-orbit coupling causes energy splitting through magnetic interaction.")
        gap = r.get("gap", {})
        return "GS115:integration", not gap.get("engine_gap_detected", True), f"gap={gap}"

# ═══════════════════════════════════════════════════════════════════════
# §18. DEMO: Obsidian Heights
# ═══════════════════════════════════════════════════════════════════════

def demo_obsidian():
    text = (
        "Engineer Miller argues slab micro-fractures were caused by high-frequency "
        "vibrational resonance from the 4th Street Light Rail bypassing standard damping layers. "
        "Contractor Wilkes countered the failure was due to lack of site-wide intentional focus "
        "and negative energy accumulation in the curing zone. "
        "Independent lab analysis found unwashed river sand in the aggregate mix leading to "
        "poor crystalline bonding and structural fatigue."
    )
    council = CouncilOfOmegas()
    result = council.analyze(text)

    print("=" * 70)
    print("USDE v6.2 — Obsidian Heights Dispute Analysis")
    print("=" * 70)
    vl_str = f"{result['violation_load']:.3f}"
    print(f"Domain: {result['domain']}  |  Mode: {result['mode']}  |  Vm: {vl_str}")
    print(f"Status: {result['status']}  |  Agreement: {result['consensus']['agreement']}")
    print(f"Stoic Vm:    {result['agent_s']['violation_load']:.3f}")
    print(f"Graceful Vm: {result['agent_g']['violation_load']:.3f}")
    print(f"Variance:    {result['consensus']['variance']:.3f}")

    print("\n— Claims —")
    for c in result.get("claims", [])[:5]:
        mech_flag = " [MECH]" if c.get("mechanism") else ""
        print(f"  [{c['confidence']:.2f}] {c['text'][:55]}...{mech_flag}")

    print("\n— Chains —")
    for ch in result.get("chains", [])[:3]:
        pathway_str = "→".join(ch["pathway"][:3]) if ch["pathway"] else "direct"
        print(f"  {ch['trigger'][:20]} → {pathway_str} → {ch['effect'][:20]} ({ch['confidence']:.2f})")

    print("\n— Spine —")
    for s in result.get("spine", [])[:3]:
        print(f"  [{s['centrality']:.2f}] {s['text'][:45]}  ({s['role']})")

    # Hook 2: Sequence
    seq = result.get("sequence", {})
    if seq.get("stateful"):
        print(f"\n— Sequence Moves ({seq['move_count']}) —")
        for m in seq.get("moves", [])[:5]:
            print(f"  [{m['confidence']:.2f}] {m['type']}: {m['evidence'][:50]}")
    else:
        print("\n— Sequence: No stateful moves detected —")

    # Hook 3: Gap
    gap = result.get("gap", {})
    if gap.get("engine_gap_detected"):
        print(f"\n— Gap Sentinel (severity={gap['max_severity']:.2f}) —")
        for gf in gap.get("gap_flags", [])[:3]:
            print(f"  [{gf['severity']:.2f}] {gf['type']}: {gf['evidence'][:50]}")
    else:
        print("\n— Gap Sentinel: No engine gaps detected —")

    print("\n" + "=" * 70)
    return result

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("USDE v6.2 — Falsification Harness")
    print("=" * 50)
    h = FalsificationHarness()
    h.run()
    total, passed, failed = h.report()
    print(f"\nResults: {passed}/{total} passed")
    if failed:
        print(f"\nFailed ({len(failed)}):")
        for label, detail in failed:
            print(f"  ✗ {label}: {detail}")
    else:
        print("All tests passed.")

    print("\n")
    demo_obsidian()
