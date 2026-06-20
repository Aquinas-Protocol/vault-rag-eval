# Live demo transcript

Captured from `https://arti0-vault-rag-eval.hf.space` (Hugging Face Space: a real `qdrant/qdrant` container + the
FastAPI app, with Neon Postgres as the lexical arm). Committed so the proof survives
link-rot — if the Space is asleep or gone, the behavior is recorded here.

### `GET /healthz`  — both stores healthy
```json
{
  "ok": true,
  "qdrant_points": 120,
  "pg_chunks": 120
}
```

### `GET /demo/d01?mode=dense&top_k=3`  — exact-identifier query, DENSE — misses leader-election (blind to the token)
```json
{
  "id": "d01",
  "query": "What does the FENCING_EPOCH_ID guard value do and why is it attached to writes?",
  "kind": "exact",
  "relevant": [
    "leader-election"
  ],
  "mode": "dense",
  "hits": [
    {
      "slug": "forward-secrecy",
      "heading": "Forward Secrecy > Details",
      "score": 0.577002,
      "snippet": "Forward Secrecy > Details The mechanism centers on ephemerality. Instead of encrypting message traffic directly under a durable private key, both parties run a fresh key-agreement step that yields a one-time session secret, often via a helper like rotate_ephemeral_keys(EPHEMERAL_"
    },
    {
      "slug": "idempotency-keys",
      "heading": "Idempotency Keys > Details",
      "score": 0.567134,
      "snippet": "Idempotency Keys > Details The server side is essentially a lookup followed by a conditional write. On receiving a request, it checks whether the supplied token already exists in its dedup store. If it does, the saved response is returned and the business logic is skipped entirel"
    },
    {
      "slug": "digital-signatures",
      "heading": "Digital Signatures > Overview",
      "score": 0.55622,
      "snippet": "Digital Signatures > Overview A digital signature lets a recipient confirm both who authored a message and that nobody altered it in transit. It relies on a key pair: the author signs with a private key kept secret, and anyone
```

### `GET /demo/d01?mode=hybrid&top_k=3`  — same query, HYBRID — Postgres lexical arm rescues leader-election to rank 1
```json
{
  "id": "d01",
  "query": "What does the FENCING_EPOCH_ID guard value do and why is it attached to writes?",
  "kind": "exact",
  "relevant": [
    "leader-election"
  ],
  "mode": "hybrid",
  "hits": [
    {
      "slug": "leader-election",
      "heading": "Leader Election > Details",
      "score": 0.027505,
      "snippet": "Leader Election > Details Detection usually relies on heartbeats and timeouts. Followers expect periodic signals from the leader; when those signals stop arriving within a deadline, a follower may start a new election. Term or epoch numbers increase with each election so that mes"
    },
    {
      "slug": "forward-secrecy",
      "heading": "Forward Secrecy > Details",
      "score": 0.016393,
      "snippet": "Forward Secrecy > Details The mechanism centers on ephemerality. Instead of encrypting message traffic directly under a durable private key, both parties run a fresh key-agreement step that yields a one-time session secret, often via a helper like rotate_ephemeral_keys(EPHEMERAL_"
    },
    {
      "slug": "idempotency-keys",
      "heading": "Idempotency Keys > Details",
      "score": 0.016129,
      "snippet": "Idempotency Keys > Details The server side is essentially a lookup followed by a conditional write. On receiving a request, it checks whether the supplied token already exists in its dedup store. If it does, the saved response is r
```

### `GET /demo/d04?mode=dense&top_k=3`  — paraphrase query, DENSE — nails it
```json
{
  "id": "d04",
  "query": "Why is reusing a set of already-open database sessions cheaper than establishing a new link for every short request?",
  "kind": "paraphrase",
  "relevant": [
    "connection-pooling"
  ],
  "mode": "dense",
  "hits": [
    {
      "slug": "connection-pooling",
      "heading": "Connection Pooling > Overview",
      "score": 0.74183,
      "snippet": "Connection Pooling > Overview Opening a fresh database connection is surprisingly expensive: it involves a network handshake, authentication, and server-side session setup. A connection pool sidesteps this by keeping a set of already-established links open and handing them out to"
    },
    {
      "slug": "connection-pooling",
      "heading": "Connection Pooling > Key Points",
      "score": 0.672316,
      "snippet": "Connection Pooling > Key Points - A pool maintains a fixed or elastic set of live connections that callers borrow and return rather than create and destroy. - Borrowing from the pool is far cheaper than a full connect, since the handshake and authentication already happened. - Si"
    },
    {
      "slug": "connection-pooling",
      "heading": "Connection Pooling > Details",
      "score": 0.634058,
      "snippet": "Connection Pooling > Details Pool sizing is a balancing act. Each open session consumes memory and a scheduler slot on the server, so the optimal pool is usually much s
```

