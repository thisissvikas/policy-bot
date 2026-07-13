from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).parent.parent


@pytest.fixture
def sample_diff() -> str:
    return (FIXTURES_DIR / "sample.diff").read_text()


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def python_diff() -> str:
    return """\
diff --git a/app/service.py b/app/service.py
index 0000000..1111111 100644
--- a/app/service.py
+++ b/app/service.py
@@ -1,5 +1,10 @@
+from models import db
+
 class UserService:
-    pass
+    def get_user(self, user_id):
+        try:
+            return db.session.query(User).get(user_id)
+        except:
+            return None
"""


@pytest.fixture
def typescript_diff() -> str:
    return """\
diff --git a/src/api/users.ts b/src/api/users.ts
index 0000000..1111111 100644
--- a/src/api/users.ts
+++ b/src/api/users.ts
@@ -1,3 +1,8 @@
+import { db } from '../database';
+
+export function getUser(id: any) {
+  const user = db.query(`SELECT * FROM users WHERE id = ${id}`);
+  return user;
+}
"""


@pytest.fixture
def mixed_diff() -> str:
    return """\
diff --git a/backend/app.py b/backend/app.py
index 0000000..1111111 100644
--- a/backend/app.py
+++ b/backend/app.py
@@ -1,3 +1,5 @@
+from flask import Flask
+app = Flask(__name__)
+
diff --git a/frontend/App.tsx b/frontend/App.tsx
index 0000000..2222222 100644
--- a/frontend/App.tsx
+++ b/frontend/App.tsx
@@ -1,3 +1,5 @@
+import React from 'react';
+export default function App() { return <div>Hello</div>; }
"""
