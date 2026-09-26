// MOCK DATA — for UI development only.
// Displayed with an amber "Mock data" notice when the backend is unreachable.
// This data is NOT real AI analysis. It will be replaced by backend API responses.

import type { Finding } from '@/types/finding'

export const mockFindings: Finding[] = [
  // ── Critical (3) ────────────────────────────────────────────────────────────
  {
    id: 'f-1',
    workflowId: 'wf-1',
    severity: 'critical',
    status: 'open',
    agent: 'security',
    title: 'Hardcoded database credential',
    description:
      'A database password is hardcoded in the source file. Anyone with repository access can read this credential.',
    location: { file: 'database.py', line: 42, function: 'get_db_connection' },
    evidence: 'DB_PASSWORD = "super_secret_password_123"',
    codeSnippet: {
      content:
        'def get_db_connection():\n    host = os.environ.get("DB_HOST", "localhost")\n    DB_PASSWORD = "super_secret_password_123"\n    return psycopg2.connect(host=host, password=DB_PASSWORD)',
      startLine: 40,
      language: 'python',
      highlightLines: [42],
    },
    whyItMatters:
      'Hardcoded credentials are exposed to anyone with repository access and cannot be rotated without a code change.',
    suggestedFix: 'Move the credential to an environment variable and access it with os.environ.get("DB_PASSWORD").',
    verificationMethod:
      'Confirm the credential is no longer present in the source file and the application reads from environment.',
    fixProposal: {
      id: 'fp-1',
      findingId: 'f-1',
      description: 'Replace hardcoded credential with environment variable lookup',
      reason:
        'Environment variables keep secrets out of source code and allow rotation without code changes.',
      risk: 'low',
      affectedFiles: ['database.py'],
      diff: {
        before: '    DB_PASSWORD = "super_secret_password_123"',
        after: '    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")',
        language: 'python',
      },
    },
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'f-2',
    workflowId: 'wf-1',
    severity: 'critical',
    status: 'approved',
    agent: 'security',
    title: 'SQL injection via unparameterized query',
    description:
      'User input is concatenated directly into a raw SQL query string without any parameterization or escaping.',
    location: { file: 'database.py', line: 103, function: 'search_todos' },
    evidence: 'query = f"SELECT * FROM todos WHERE title LIKE \'%{search_term}%\'"',
    codeSnippet: {
      content:
        'def search_todos(search_term: str):\n    query = f"SELECT * FROM todos WHERE title LIKE \'%{search_term}%\'"\n    result = engine.execute(query)\n    return result.fetchall()',
      startLine: 101,
      language: 'python',
      highlightLines: [102],
    },
    whyItMatters:
      'An attacker can inject arbitrary SQL, potentially reading or modifying any data in the database, including credentials and user records.',
    suggestedFix:
      'Use the ORM filter method: db.query(Todo).filter(Todo.title.contains(search_term))',
    verificationMethod:
      'Test with a search term containing SQL metacharacters and confirm the query is safe.',
    fixProposal: {
      id: 'fp-2',
      findingId: 'f-2',
      description: 'Replace raw SQL query with parameterized ORM filter',
      reason:
        'SQLAlchemy ORM methods automatically handle escaping, preventing injection attacks.',
      risk: 'medium',
      affectedFiles: ['database.py'],
      diff: {
        before:
          '    query = f"SELECT * FROM todos WHERE title LIKE \'%{search_term}%\'"\n    result = engine.execute(query)\n    return result.fetchall()',
        after:
          '    return db.query(Todo).filter(Todo.title.contains(search_term)).all()',
        language: 'python',
      },
      approvedAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    },
    createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
  },
  {
    id: 'f-3',
    workflowId: 'wf-1',
    severity: 'critical',
    status: 'verified',
    agent: 'security',
    title: 'Authentication bypass via missing token validation',
    description:
      'The /admin/users endpoint accepts requests without validating the JWT token signature, allowing unauthenticated access.',
    location: { file: 'routes/admin.py', line: 14, function: 'list_users' },
    evidence: '# TODO: add token validation\n@router.get("/admin/users")\nasync def list_users(db: Session = Depends(get_db)):',
    whyItMatters:
      'Any client can enumerate all users, including their email addresses and account metadata, without authentication.',
    suggestedFix:
      'Add the get_current_user dependency: async def list_users(current_user = Depends(get_current_user), ...)',
    verificationMethod:
      'Send a request without an Authorization header and confirm the response is 401.',
    createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
  },

  // ── High (4) ─────────────────────────────────────────────────────────────────
  {
    id: 'f-4',
    workflowId: 'wf-1',
    severity: 'high',
    status: 'open',
    agent: 'code_review',
    title: 'Missing 404 handler for Todo endpoint',
    description:
      'The GET /todos/{id} endpoint does not handle the case where the Todo record does not exist, returning an unhandled exception.',
    location: { file: 'routes.py', line: 87, function: 'get_todo' },
    evidence:
      'todo = db.query(Todo).filter(Todo.id == todo_id).first()\nreturn todo  # No None check',
    whyItMatters:
      'Clients receive a 500 Internal Server Error instead of a descriptive 404, breaking API consumers.',
    suggestedFix:
      'Add a None check and raise HTTPException(status_code=404, detail="Todo not found") when the record is missing.',
    verificationMethod:
      'Send a GET request with a non-existent ID and confirm the response is 404.',
    fixProposal: {
      id: 'fp-4',
      findingId: 'f-4',
      description: 'Add a 404 guard for missing Todo records',
      reason:
        'Without a None check the ORM returns None which FastAPI cannot serialize, causing a 500 response.',
      risk: 'low',
      affectedFiles: ['routes.py'],
      diff: {
        before:
          '    todo = db.query(Todo).filter(Todo.id == todo_id).first()\n    return todo',
        after:
          '    todo = db.query(Todo).filter(Todo.id == todo_id).first()\n    if not todo:\n        raise HTTPException(status_code=404, detail="Todo not found")\n    return todo',
        language: 'python',
      },
    },
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'f-5',
    workflowId: 'wf-1',
    severity: 'high',
    status: 'open',
    agent: 'code_review',
    title: 'Uncaught database exception on create operation',
    description:
      'The POST /todos endpoint does not wrap the database insert in a try/except block. A constraint violation or connection error propagates as a 500.',
    location: { file: 'routes.py', line: 55, function: 'create_todo' },
    evidence:
      '@router.post("/todos", response_model=TodoResponse)\nasync def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):\n    db_todo = Todo(**todo.dict())\n    db.add(db_todo)\n    db.commit()  # can raise IntegrityError\n    return db_todo',
    whyItMatters:
      'Database errors expose raw exception tracebacks to the client in development mode and cause unhandled 500 errors in production.',
    suggestedFix:
      'Wrap the db.commit() call in a try/except block catching SQLAlchemyError and returning an appropriate HTTPException.',
    verificationMethod:
      'Submit a duplicate title and confirm the response is 409 Conflict with a clear error message.',
    fixProposal: {
      id: 'fp-5',
      findingId: 'f-5',
      description: 'Add exception handling around database insert',
      reason:
        'Catching SQLAlchemyError allows the API to return structured error responses instead of raw tracebacks.',
      risk: 'low',
      affectedFiles: ['routes.py'],
      diff: {
        before:
          '    db.add(db_todo)\n    db.commit()\n    db.refresh(db_todo)\n    return db_todo',
        after:
          '    db.add(db_todo)\n    try:\n        db.commit()\n        db.refresh(db_todo)\n    except SQLAlchemyError as e:\n        db.rollback()\n        raise HTTPException(status_code=409, detail="Could not create todo.")\n    return db_todo',
        language: 'python',
      },
    },
    createdAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'f-6',
    workflowId: 'wf-1',
    severity: 'high',
    status: 'rejected',
    agent: 'test_analysis',
    title: 'No integration tests for DELETE endpoint',
    description:
      'The DELETE /todos/{id} endpoint has zero test coverage. No tests verify cascade behavior, idempotency, or the 404 response for missing records.',
    location: { file: 'tests/test_todos.py', line: 1 },
    evidence: '# DELETE /todos/{id} — no tests found',
    whyItMatters:
      'Without tests, regressions in the delete operation can go undetected, potentially causing data integrity issues.',
    suggestedFix:
      'Add tests for: successful deletion (204), deletion of non-existent ID (404), and duplicate deletion (idempotency).',
    verificationMethod: 'Run pytest and confirm all three new test cases pass.',
    fixProposal: {
      id: 'fp-6',
      findingId: 'f-6',
      description: 'Generate integration tests for the DELETE /todos/{id} endpoint',
      reason: 'Automated test coverage prevents regressions and documents expected behavior.',
      risk: 'low',
      affectedFiles: ['tests/test_todos.py'],
      rejectedAt: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
      rejectionReason:
        'Test generation will be handled in the dedicated testing sprint. Keeping finding open for tracking.',
    },
    createdAt: new Date(Date.now() - 2.5 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
  },
  {
    id: 'f-7',
    workflowId: 'wf-1',
    severity: 'high',
    status: 'fixed',
    agent: 'code_review',
    title: 'N+1 query in list endpoint',
    description:
      'The GET /todos endpoint executes a separate database query for each todo item to fetch its tags, resulting in N+1 queries.',
    location: { file: 'routes.py', line: 30, function: 'list_todos' },
    evidence:
      'todos = db.query(Todo).all()\nfor todo in todos:\n    todo.tags = db.query(Tag).filter(Tag.todo_id == todo.id).all()',
    whyItMatters:
      'For 100 todos, this executes 101 database queries. Performance degrades linearly with dataset size.',
    suggestedFix:
      'Use SQLAlchemy joinedload() or selectinload() to eagerly fetch tags in a single query.',
    verificationMethod:
      'Enable SQLAlchemy query logging and confirm list endpoint executes at most 2 queries.',
    createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  },

  // ── Medium (4) ───────────────────────────────────────────────────────────────
  {
    id: 'f-8',
    workflowId: 'wf-1',
    severity: 'medium',
    status: 'open',
    agent: 'test_analysis',
    title: 'No test coverage for error paths',
    description: 'The error handling branches in the Todo CRUD operations have zero test coverage.',
    location: { file: 'tests/test_todos.py', line: 1 },
    evidence: 'Coverage report: routes.py error branches — 0%',
    whyItMatters:
      'Untested error paths may silently fail in production, causing data corruption or unexpected behavior.',
    suggestedFix:
      'Add tests that simulate database failures and verify the API returns appropriate error responses.',
    verificationMethod: 'Run test coverage and confirm error branches reach at least 80%.',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'f-9',
    workflowId: 'wf-1',
    severity: 'medium',
    status: 'open',
    agent: 'documentation',
    title: 'API endpoints missing OpenAPI descriptions',
    description: 'Six API endpoints lack summary and description fields in their route decorators.',
    location: { file: 'routes.py', line: 45 },
    evidence: '@router.post("/todos")\nasync def create_todo(...)  # No description',
    whyItMatters:
      'Auto-generated API docs are incomplete, making integration harder for API consumers.',
    suggestedFix: 'Add summary and description parameters to each route decorator.',
    verificationMethod:
      'Check /docs in the running application and confirm all endpoints have descriptions.',
    fixProposal: {
      id: 'fp-9',
      findingId: 'f-9',
      description: 'Add OpenAPI summary and description to all route decorators',
      reason: 'FastAPI uses these fields to generate /docs documentation.',
      risk: 'low',
      affectedFiles: ['routes.py'],
    },
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'f-10',
    workflowId: 'wf-1',
    severity: 'medium',
    status: 'verification_failed',
    agent: 'test_analysis',
    title: 'Pagination not tested for boundary conditions',
    description:
      'The GET /todos endpoint supports limit and offset query parameters, but no tests cover page=0, limit=0, or limit exceeding the total record count.',
    location: { file: 'tests/test_todos.py', line: 78 },
    evidence: '# Only happy-path pagination tested (limit=10, offset=0)',
    whyItMatters:
      'Boundary conditions are common sources of off-by-one errors that can corrupt pagination state or return incorrect result sets.',
    suggestedFix:
      'Add parametrized tests for limit=0, offset=0, offset greater than total, and limit greater than total.',
    verificationMethod: 'Run pytest -k pagination and confirm all boundary cases pass.',
    createdAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
  },
  {
    id: 'f-11',
    workflowId: 'wf-1',
    severity: 'medium',
    status: 'in_review',
    agent: 'code_review',
    title: 'Magic numbers in status validation',
    description:
      'Todo status validation uses raw integer comparisons (0, 1, 2) instead of an enum or named constants.',
    location: { file: 'models.py', line: 34, function: 'validate_status' },
    evidence: 'if status not in [0, 1, 2]: raise ValueError("Invalid status")',
    whyItMatters:
      'Magic numbers make the code harder to maintain and understand. Adding a new status requires finding all occurrences.',
    suggestedFix:
      'Define a Python enum: class TodoStatus(IntEnum): PENDING=0, IN_PROGRESS=1, DONE=2 and use it throughout.',
    verificationMethod: 'Confirm all status comparisons use the enum values.',
    fixProposal: {
      id: 'fp-11',
      findingId: 'f-11',
      description: 'Replace magic number status checks with a TodoStatus enum',
      reason:
        'Enums provide named constants that are self-documenting and prevent invalid state assignments.',
      risk: 'medium',
      affectedFiles: ['models.py', 'routes.py'],
      diff: {
        before: 'if status not in [0, 1, 2]:\n    raise ValueError("Invalid status")',
        after:
          'class TodoStatus(IntEnum):\n    PENDING = 0\n    IN_PROGRESS = 1\n    DONE = 2\n\nif status not in TodoStatus.__members__.values():\n    raise ValueError("Invalid status")',
        language: 'python',
      },
    },
    createdAt: new Date(Date.now() - 1.5 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
  },

  // ── Low (2) ──────────────────────────────────────────────────────────────────
  {
    id: 'f-12',
    workflowId: 'wf-1',
    severity: 'low',
    status: 'dismissed',
    agent: 'code_review',
    title: 'Inconsistent variable naming convention',
    description:
      'Some variables use camelCase while the rest of the codebase uses snake_case.',
    location: { file: 'models.py', line: 18 },
    evidence: 'createdAt = Column(DateTime)  # Should be created_at',
    whyItMatters:
      'Inconsistent naming reduces readability and violates PEP 8 conventions.',
    suggestedFix:
      'Rename createdAt and updatedAt to created_at and updated_at throughout the codebase.',
    verificationMethod: 'Run a linter and confirm no naming convention violations remain.',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: 'f-13',
    workflowId: 'wf-1',
    severity: 'low',
    status: 'open',
    agent: 'documentation',
    title: 'Missing docstrings on public functions',
    description:
      'Fourteen public functions in routes.py and models.py lack docstrings, reducing auto-generated documentation quality.',
    location: { file: 'routes.py', line: 1 },
    evidence: 'async def create_todo(...):  # no docstring\nasync def list_todos(...):  # no docstring',
    whyItMatters:
      'Missing docstrings reduce the usefulness of auto-generated API documentation and IDE help text.',
    suggestedFix:
      'Add a one-line docstring to each public function describing its purpose and return value.',
    verificationMethod: 'Run pydocstyle and confirm no missing docstring warnings.',
    fixProposal: {
      id: 'fp-13',
      findingId: 'f-13',
      description: 'Add docstrings to all undocumented public functions',
      reason: 'Docstrings are included in FastAPI auto-generated OpenAPI docs.',
      risk: 'low',
      affectedFiles: ['routes.py', 'models.py'],
    },
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
]
