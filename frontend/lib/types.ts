// Mirrors backend/app/schemas.py. Hand-written rather than generated: the API
// has eight shapes and a generator would be more machinery than it saves.

export type Intent = 'chat' | 'knowledge' | 'code';

/** What became of a code proposal, read from the following turn's trace. */
export type Outcome = 'pending' | 'approved' | 'denied' | 'revised';

export interface Citation {
  source: string;
  heading: string;
  text: string;
  score: number;
}

export interface TraceEvent {
  node: string;
  detail: string;
  elapsed_ms: number;
}

export interface FileEdit {
  path: string;
  new_content: string;
}

export interface CodeProposal {
  summary: string;
  rationale: string;
  verification: string;
  adrs_consulted: string[];
  branch: string;
  commit_message: string;
  edits: FileEdit[];
}

export interface CheckResult {
  name: string;
  passed: boolean;
  output: string;
}

export interface PullRequest {
  branch: string;
  title: string;
  body: string;
  diff: string;
  checks: CheckResult[];
}

export interface ChatResponse {
  thread_id: string;
  // 'awaiting_approval' means the graph is suspended and nothing has been
  // written yet. It is the only state in which /approve is meaningful.
  status: 'complete' | 'awaiting_approval';
  intent: Intent | null;
  reply: string;
  citations: Citation[];
  trace: TraceEvent[];
  proposal: CodeProposal | null;
  diff: string;
  // Review rules the proposal still breaks. Shown before the approve button,
  // never after: a reviewer needs it while the decision is still open.
  violations: string[];
  pull_request: PullRequest | null;
}

export interface Health {
  status: string;
  corpus_documents: number;
}
