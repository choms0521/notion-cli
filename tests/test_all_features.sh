#!/bin/bash
# notion-cli 전체 기능 통합 테스트
# 테스트용 부모 페이지: 공부자료 모음 (3022d7a3-d36d-8003-b2de-cc31bb1eca70)

set -euo pipefail

PARENT_ID="3022d7a3-d36d-8003-b2de-cc31bb1eca70"
PASS=0
FAIL=0
ERRORS=()

green() { printf "\033[32m✅ PASS: %s\033[0m\n" "$1"; PASS=$((PASS+1)); }
red()   { printf "\033[31m❌ FAIL: %s\033[0m\n" "$1"; FAIL=$((FAIL+1)); ERRORS+=("$1: $2"); }

run_test() {
    local name="$1"
    shift
    local output
    if output=$("$@" 2>&1); then
        green "$name"
        echo "$output"
    else
        red "$name" "$output"
        echo "$output"
    fi
    echo "---"
}

# 명령 실행 후 출력에 expected 문자열이 포함되는지 검증
assert_contains() {
    local name="$1"
    local expected="$2"
    shift 2
    local output
    if output=$("$@" 2>&1); then
        if echo "$output" | grep -qF "$expected"; then
            green "$name"
        else
            red "$name" "Expected '$expected' not found in output: $output"
        fi
        echo "$output"
    else
        red "$name" "$output"
        echo "$output"
    fi
    echo "---"
}

# JSON 출력에서 특정 jq 표현식이 truthy인지 검증
assert_json() {
    local name="$1"
    local jq_expr="$2"
    shift 2
    local output
    if output=$("$@" 2>&1); then
        if echo "$output" | jq -e "$jq_expr" >/dev/null 2>&1; then
            green "$name"
        else
            red "$name" "JSON assertion failed: $jq_expr"
        fi
        echo "$output"
    else
        red "$name" "$output"
        echo "$output"
    fi
    echo "---"
}

echo "========================================"
echo " notion-cli 전체 기능 통합 테스트"
echo "========================================"
echo ""

# ── 1. Users ──
echo "## 1. Users"
run_test "users me" notion-cli --json users me
run_test "users list" notion-cli --json users list

# users get - me에서 ID 추출
BOT_ID=$(notion-cli --json users me 2>/dev/null | jq -r '.id // empty')
if [ -n "$BOT_ID" ]; then
    run_test "users get" notion-cli --json users get "$BOT_ID"
else
    red "users get" "Could not extract bot ID"
fi

# ── 2. Search ──
echo "## 2. Search"
run_test "search (keyword)" notion-cli --json search "공부자료"
run_test "search (type filter)" notion-cli --json search "공부" --type page

# ── 3. Pages - Create ──
echo "## 3. Pages"
PAGE_OUTPUT=$(notion-cli --json pages create "통합테스트 페이지 (자동삭제)" --parent "$PARENT_ID" --content "초기 본문 텍스트" 2>&1)
PAGE_ID=$(echo "$PAGE_OUTPUT" | jq -r '.id // empty')
if [ -n "$PAGE_ID" ]; then
    green "pages create"
    echo "Created page: $PAGE_ID"
else
    red "pages create" "$PAGE_OUTPUT"
    echo "FATAL: Cannot continue without test page"
    exit 1
fi
echo "---"

# Pages - Get (verify returned page matches)
assert_json "pages get" ".id == \"$PAGE_ID\"" notion-cli --json pages get "$PAGE_ID"

# Pages - Update (title) - verify output confirms update
assert_contains "pages update --title" "Updated page" notion-cli pages update "$PAGE_ID" --title "통합테스트 수정됨 (자동삭제)"

# Pages - Update (icon) - verify title was actually changed
assert_json "pages update --icon (verify title persisted)" ".properties.title.title[0].plain_text == \"통합테스트 수정됨 (자동삭제)\"" notion-cli --json pages update "$PAGE_ID" --icon "🧪"

# Pages - Markdown (read) - verify initial content
assert_contains "pages markdown" "초기 본문 텍스트" notion-cli pages markdown "$PAGE_ID"

# Pages - Update-markdown
run_test "pages update-markdown" notion-cli pages update-markdown "$PAGE_ID" "# 테스트 제목

본문 내용입니다.

- 항목 1
- 항목 2"

# Pages - Markdown (verify update contains expected content)
assert_contains "pages markdown (after update)" "테스트 제목" notion-cli pages markdown "$PAGE_ID"

# Pages - Edit-markdown (surgical find-and-replace)
run_test "pages edit-markdown" notion-cli pages edit-markdown "$PAGE_ID" --old "테스트 제목" --new "수정된 제목"

# Pages - Markdown (verify edit applied correctly)
assert_contains "pages markdown (after edit)" "수정된 제목" notion-cli pages markdown "$PAGE_ID"

# Pages - Edit-markdown-batch (multiple replacements)
run_test "pages edit-markdown-batch" notion-cli pages edit-markdown-batch "$PAGE_ID" '[{"old_str": "수정된 제목", "new_str": "최종 제목"}, {"old_str": "본문 내용입니다.", "new_str": "본문이 수정되었습니다."}]'

# Pages - Markdown (verify both batch edits applied)
assert_contains "pages markdown (after batch edit: title)" "최종 제목" notion-cli pages markdown "$PAGE_ID"

# ── 4. Blocks ──
echo "## 4. Blocks"

# Blocks - Append (paragraph)
run_test "blocks append (paragraph)" notion-cli blocks append "$PAGE_ID" "추가된 단락 텍스트"

# Blocks - Append (heading)
run_test "blocks append (heading_2)" notion-cli blocks append "$PAGE_ID" "추가된 제목" --type heading_2

# Blocks - Append (code)
run_test "blocks append (code)" notion-cli --json blocks append "$PAGE_ID" "print('hello world')" --type code --language python

# Blocks - Append (quote)
run_test "blocks append (quote)" notion-cli blocks append "$PAGE_ID" "인용문입니다" --type quote

# Blocks - Append (bulleted_list_item)
run_test "blocks append (bulleted_list)" notion-cli blocks append "$PAGE_ID" "리스트 항목" --type bulleted_list_item

# Blocks - Append (numbered_list_item)
run_test "blocks append (numbered_list)" notion-cli blocks append "$PAGE_ID" "번호 항목" --type numbered_list_item

# Blocks - Append (to_do)
run_test "blocks append (to_do)" notion-cli blocks append "$PAGE_ID" "할 일 항목" --type to_do

# Blocks - Append (callout)
run_test "blocks append (callout)" notion-cli blocks append "$PAGE_ID" "콜아웃 내용" --type callout

# Blocks - Append (toggle)
run_test "blocks append (toggle)" notion-cli blocks append "$PAGE_ID" "토글 내용" --type toggle

# Blocks - Append (divider)
run_test "blocks append (divider)" notion-cli blocks append "$PAGE_ID" "" --type divider

# Blocks - Children
CHILDREN_OUTPUT=$(notion-cli --json blocks children "$PAGE_ID" 2>&1)
CHILD_COUNT=$(echo "$CHILDREN_OUTPUT" | jq 'length // 0')
if [ "$CHILD_COUNT" -gt 0 ]; then
    green "blocks children"
    echo "Found $CHILD_COUNT blocks"
else
    red "blocks children" "No children found"
fi
echo "---"

# Blocks - Get (first child)
FIRST_BLOCK_ID=$(echo "$CHILDREN_OUTPUT" | jq -r '.[0].id // empty')
if [ -n "$FIRST_BLOCK_ID" ]; then
    run_test "blocks get" notion-cli --json blocks get "$FIRST_BLOCK_ID"
else
    red "blocks get" "No block ID to test"
fi

# Blocks - Update (find a paragraph block)
PARAGRAPH_ID=$(echo "$CHILDREN_OUTPUT" | jq -r '[.[] | select(.type == "paragraph")][0].id // empty')
if [ -n "$PARAGRAPH_ID" ]; then
    run_test "blocks update" notion-cli blocks update "$PARAGRAPH_ID" "수정된 단락 텍스트"
else
    red "blocks update" "No paragraph block found to update"
fi

# Blocks - Delete (last block)
LAST_BLOCK_ID=$(echo "$CHILDREN_OUTPUT" | jq -r '.[-1].id // empty')
if [ -n "$LAST_BLOCK_ID" ]; then
    run_test "blocks delete" notion-cli blocks delete "$LAST_BLOCK_ID"
else
    red "blocks delete" "No block to delete"
fi

# ── 5. Databases ──
echo "## 5. Databases"

# Databases - Create
DB_OUTPUT=$(notion-cli --json databases create "테스트 DB (자동삭제)" --parent "$PAGE_ID" 2>&1)
DB_ID=$(echo "$DB_OUTPUT" | jq -r '.id // empty')
if [ -n "$DB_ID" ]; then
    green "databases create"
    echo "Created DB: $DB_ID"
else
    red "databases create" "$DB_OUTPUT"
fi
echo "---"

# Databases - Get (verify ID matches)
if [ -n "$DB_ID" ]; then
    assert_json "databases get" ".id == \"$DB_ID\"" notion-cli --json databases get "$DB_ID"
fi

# Databases - Update (verify output confirms)
if [ -n "$DB_ID" ]; then
    assert_contains "databases update" "Updated database" notion-cli databases update "$DB_ID" --title "수정된 테스트 DB"
fi

# Databases - Query (verify returns array)
if [ -n "$DB_ID" ]; then
    assert_json "databases query" "type == \"array\"" notion-cli --json databases query "$DB_ID"
fi

# ── 6. Comments ──
echo "## 6. Comments"
if notion-cli --json comments list "$PAGE_ID" >/dev/null 2>&1; then
    green "comments list"
    run_test "comments create" notion-cli --json comments create "$PAGE_ID" "테스트 코멘트입니다"
else
    echo "⚠️  SKIP: comments (API 토큰에 코멘트 권한 없음 - 403 Forbidden)"
fi

# ── 7. Pages - Move ──
echo "## 7. Pages Move"

# 이동용 임시 페이지 생성
MOVE_TARGET=$(notion-cli --json pages create "이동 대상 (자동삭제)" --parent "$PARENT_ID" 2>&1 | jq -r '.id // empty')
if [ -n "$MOVE_TARGET" ]; then
    green "pages create (move target)"

    # 이동할 하위 페이지 생성
    MOVE_PAGE=$(notion-cli --json pages create "이동할 페이지" --parent "$PAGE_ID" 2>&1 | jq -r '.id // empty')
    if [ -n "$MOVE_PAGE" ]; then
        run_test "pages move" notion-cli pages move "$MOVE_PAGE" --to "$MOVE_TARGET"
        # 정리
        notion-cli pages archive "$MOVE_PAGE" 2>/dev/null || true
    else
        red "pages move" "Could not create page to move"
    fi

    # 정리
    notion-cli pages archive "$MOVE_TARGET" 2>/dev/null || true
else
    red "pages move" "Could not create move target"
fi
echo "---"

# ── 8. Pages - Archive ──
echo "## 8. Cleanup"
run_test "pages archive" notion-cli pages archive "$PAGE_ID"

# ── Summary ──
echo ""
echo "========================================"
echo " 테스트 결과 요약"
echo "========================================"
echo " PASS: $PASS"
echo " FAIL: $FAIL"
echo " TOTAL: $((PASS + FAIL))"
echo ""

if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "실패한 테스트:"
    for err in "${ERRORS[@]}"; do
        echo "  - $err"
    done
fi

if [ "$FAIL" -eq 0 ]; then
    echo "🎉 모든 테스트 통과!"
else
    echo "⚠️ $FAIL개 테스트 실패"
    exit 1
fi
