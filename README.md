# notion-cli

Notion API CLI tool built with Python and Click.

Manage pages, databases, blocks, and more from the command line.

## Installation

```bash
# From source
git clone https://github.com/your-username/notion-cli.git
cd notion-cli
pip install -e .

# Verify
notion-cli --help
```

### Requirements

- Python 3.10+
- Notion Internal Integration Token

## Notion Token Setup

### 1. Integration 생성

1. [Notion Integrations](https://www.notion.so/my-integrations) 접속
2. **New integration** 클릭
3. 이름 입력 (예: `my-cli`)
4. 워크스페이스 선택
5. Capabilities에서 필요한 권한 체크:
   - **Read content** - 페이지/DB 조회
   - **Update content** - 페이지/블록 수정
   - **Insert content** - 페이지/블록 생성
   - **Read comments** / **Create comments** - 코멘트 기능 사용 시
6. **Save** 후 `ntn_` 으로 시작하는 토큰 복사

### 2. 페이지에 Integration 연결

> Integration은 명시적으로 연결된 페이지에만 접근할 수 있습니다.

1. Notion에서 접근할 페이지 열기
2. 우측 상단 `...` 메뉴 클릭
3. **Connections** > 생성한 Integration 선택
4. 하위 페이지에도 자동 적용됨

### 3. 토큰 설정 (택 1)

```bash
# 방법 1: CLI에 저장 (권장)
notion-cli config set-token "ntn_your_token_here"

# 방법 2: 환경변수
export NOTION_API_KEY="ntn_your_token_here"

# 방법 3: 명령어마다 직접 전달
notion-cli --token "ntn_your_token_here" search "test"
```

토큰은 `~/.notion-cli/config.json`에 저장됩니다.

## Usage

### Global Options

```bash
notion-cli --json <command>   # JSON 출력
notion-cli --token <token> <command>  # 토큰 직접 지정
```

> `--json`, `--token`은 서브커맨드 **앞**에 위치해야 합니다.

### Pages

```bash
# 생성
notion-cli pages create "My Page" --parent <parent-id>
notion-cli pages create "DB Row" --parent <db-id> --parent-type database_id

# 조회
notion-cli --json pages get <page-id>
notion-cli pages markdown <page-id>

# 수정
notion-cli pages update <page-id> --title "New Title"
notion-cli pages update <page-id> --icon "🔥"
notion-cli pages update <page-id> --cover "https://example.com/image.jpg"
notion-cli pages update <page-id> --property '{"Status": {"select": {"name": "Done"}}}'

# 마크다운으로 내용 교체
notion-cli pages update-markdown <page-id> "# Hello World"

# 마크다운 부분 수정 (find-and-replace)
notion-cli pages edit-markdown <page-id> --old "기존 텍스트" --new "새 텍스트"
notion-cli pages edit-markdown <page-id> --old "반복 텍스트" --new "교체" --replace-all

# 마크다운 일괄 수정 (최대 100건)
notion-cli pages edit-markdown-batch <page-id> '[{"old_str": "A", "new_str": "B"}, {"old_str": "C", "new_str": "D"}]'

# 이동 / 아카이브
notion-cli pages move <page-id> --to <new-parent-id>
notion-cli pages archive <page-id>
```

### Blocks

```bash
# 조회
notion-cli --json blocks children <page-id>
notion-cli --json blocks get <block-id>

# 추가
notion-cli blocks append <page-id> "Hello"
notion-cli blocks append <page-id> "Title" --type heading_1
notion-cli blocks append <page-id> "print('hi')" --type code --language python
notion-cli blocks append <page-id> "" --type divider

# 수정 (블록 타입 자동 감지)
notion-cli blocks update <block-id> "Updated text"
notion-cli blocks update <block-id> "new code" --language javascript

# 삭제
notion-cli blocks delete <block-id>
```

**Supported block types:** paragraph, heading_1, heading_2, heading_3, bulleted_list_item, numbered_list_item, to_do, quote, callout, code, divider, toggle

### Databases

```bash
# 조회
notion-cli --json databases get <db-id>

# 생성
notion-cli databases create "My DB" --parent <page-id>

# 수정
notion-cli databases update <db-id> --title "New Name"

# 쿼리
notion-cli --json databases query <db-or-datasource-id> --all
notion-cli --json databases query <id> --filter '{"property": "Status", "select": {"equals": "Done"}}'
```

> DB ID와 data_source ID가 다를 수 있습니다. 어느 쪽을 전달해도 자동으로 resolve됩니다.

### Search

```bash
notion-cli --json search "keyword"
notion-cli --json search "keyword" --type page
notion-cli --json search "" --type database --all
```

### Comments

```bash
notion-cli --json comments list <page-id>
notion-cli --json comments create <page-id> "My comment"
```

> Integration에 코멘트 권한이 필요합니다.

### Users

```bash
notion-cli --json users me
notion-cli --json users list
notion-cli --json users get <user-id>
```

### Config

```bash
notion-cli config set-token <token>
notion-cli config remove-token
```

## Examples

```bash
# 페이지 생성 후 코드 블록 추가
PAGE_ID=$(notion-cli --json pages create "Python Notes" --parent <parent-id> | jq -r '.id')
notion-cli blocks append "$PAGE_ID" "Code Examples" --type heading_2
notion-cli blocks append "$PAGE_ID" "print('hello world')" --type code --language python

# 하위 페이지 목록 가져오기
notion-cli --json blocks children <page-id> \
  | jq -r '.[] | select(.type == "child_page") | .child_page.title'

# 페이지 마크다운으로 내용 교체
notion-cli pages update-markdown <page-id> "$(cat my-document.md)"

# 페이지 마크다운 부분 수정 (전체 교체 없이 특정 텍스트만 변경)
notion-cli pages edit-markdown <page-id> --old "Draft" --new "Final"

# 여러 곳 한번에 수정
notion-cli pages edit-markdown-batch <page-id> \
  '[{"old_str": "v1.0", "new_str": "v1.1"}, {"old_str": "TODO", "new_str": "DONE"}]'

# DB 필터 쿼리
notion-cli --json databases query <id> \
  --filter '{"property": "Priority", "select": {"equals": "High"}}' \
  --sorts '[{"property": "Created", "direction": "descending"}]'
```

## Project Structure

```
notion-cli/
├── setup.py
├── tests/
│   └── test_all_features.sh
└── cli_anything/notion/
    ├── notion_cli.py          # CLI entry point (Click)
    ├── core/
    │   ├── pages.py           # Pages CRUD + markdown
    │   ├── blocks.py          # Blocks append/update/delete
    │   ├── databases.py       # Databases create/query
    │   ├── search.py          # Search
    │   ├── comments.py        # Comments
    │   └── users.py           # Users
    └── utils/
        ├── auth.py            # Token management
        ├── output.py          # JSON/table formatting
        └── pagination.py      # Auto-pagination
```

## Dependencies

- [click](https://click.palletsprojects.com/) >= 8.0.0
- [notion-client](https://github.com/ramnes/notion-sdk-py) >= 3.0.0
- [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/) >= 3.0.0

## License

MIT
