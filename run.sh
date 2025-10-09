#!/bin/bash
echo "Starting Live Data Analysis by Masumi (ADA)..."
uvicorn backend.app:app --reload
