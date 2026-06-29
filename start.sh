#!/bin/bash
set -e

echo "=== Sovereign Security Platform ==="
echo ""

# Backend
echo "[1/2] تثبيت وتشغيل Backend..."
cd backend
pip install -r requirements.txt -q
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "Backend يعمل على http://localhost:8000"

# Frontend
cd ../frontend
echo "[2/2] تثبيت وتشغيل Frontend..."
npm install --silent
npm run dev &
FRONTEND_PID=$!
echo "Frontend يعمل على http://localhost:3000"

echo ""
echo "✓ المنصة تعمل!"
echo "  - واجهة المستخدم: http://localhost:3000"
echo "  - API: http://localhost:8000"
echo "  - توثيق API: http://localhost:8000/docs"
echo ""
echo "اضغط Ctrl+C للإيقاف"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
