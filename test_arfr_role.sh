#!/bin/bash

echo "========================================="
echo "Testing ARFR Role Stability"
echo "========================================="

BASE_URL="http://127.0.0.1:5000"
ARFR_ROUTES=(
    "/arfr"
    "/arfr/dashboard"
    "/arfr/insurers"
    "/arfr/reports"
    "/arfr/violations"
    "/arfr/market"
    "/arfr/stress"
    "/arfr/compliance"
)

echo ""
echo "Testing all ARFR routes..."
echo ""

for route in "${ARFR_ROUTES[@]}"; do
    echo "Testing: $BASE_URL$route"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$route")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✓ HTTP $HTTP_CODE - OK"
    else
        echo "  ✗ HTTP $HTTP_CODE - FAILED"
    fi
done

echo ""
echo "========================================="
echo "Testing insurer routes don't break..."
echo "========================================="

INSURER_ROUTES=(
    "/"
    "/ifrs9"
    "/ifrs17"
    "/calculation"
    "/solvency2"
)

echo ""

for route in "${INSURER_ROUTES[@]}"; do
    echo "Testing: $BASE_URL$route"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$route")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✓ HTTP $HTTP_CODE - OK"
    else
        echo "  ✗ HTTP $HTTP_CODE - FAILED"
    fi
done

echo ""
echo "========================================="
echo "All tests completed!"
echo "========================================="
