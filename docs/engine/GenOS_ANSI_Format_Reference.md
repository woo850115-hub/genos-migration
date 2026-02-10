# GenOS ANSI 컬러 포맷 레퍼런스

**Version**: 1.0
**Last Updated**: 2026-02-10
**Author**: 누렁이

---

## 1. 개요

GenOS는 4개 게임(tbaMUD, Simoon, 3eyes, 10woongi)의 서로 다른 컬러 코드를 **하나의 공통 포맷**으로 통일한다. 마이그레이션 도구가 원본 코드를 GenOS 포맷으로 변환하고, 엔진이 GenOS 포맷을 ANSI 이스케이프로 최종 출력한다.

```
원본 소스 → 마이그레이션 도구 → GenOS 포맷 (DB/Lua 저장) → 엔진 → ANSI 이스케이프 (클라이언트)
```

### 포맷 문법

```
{코드명}
```

- 중괄호(`{`, `}`)로 감싼 코드명
- 코드명은 영문, 콜론(`:`), 쉼표(`,`), 숫자 조합
- 대소문자 구분: 소문자 = dark/standard, 대문자 = bright

---

## 2. 리셋

| GenOS 코드 | SGR 코드 | ANSI 이스케이프 | 설명 |
|-----------|----------|----------------|------|
| `{reset}` | 0 | `\x1b[0m` | 모든 속성 초기화 |

---

## 3. 텍스트 포맷

| GenOS 코드 | SGR 코드 | ANSI 이스케이프 | 설명 |
|-----------|----------|----------------|------|
| `{bold}` | 1 | `\x1b[1m` | 굵게 / 밝게 |
| `{dim}` | 2 | `\x1b[2m` | 흐리게 |
| `{italic}` | 3 | `\x1b[3m` | 기울임 |
| `{underline}` | 4 | `\x1b[4m` | 밑줄 |
| `{blink}` | 5 | `\x1b[5m` | 느린 깜빡임 |
| `{rapid_blink}` | 6 | `\x1b[6m` | 빠른 깜빡임 |
| `{reverse}` | 7 | `\x1b[7m` | 전경/배경 반전 |
| `{hidden}` | 8 | `\x1b[8m` | 숨김 (비밀번호 등) |
| `{strikethrough}` | 9 | `\x1b[9m` | 취소선 |

### 포맷 해제

| GenOS 코드 | SGR 코드 | ANSI 이스케이프 | 설명 |
|-----------|----------|----------------|------|
| `{/bold}` | 22 | `\x1b[22m` | 굵게 해제 |
| `{/dim}` | 22 | `\x1b[22m` | 흐리게 해제 |
| `{/italic}` | 23 | `\x1b[23m` | 기울임 해제 |
| `{/underline}` | 24 | `\x1b[24m` | 밑줄 해제 |
| `{/blink}` | 25 | `\x1b[25m` | 깜빡임 해제 |
| `{/reverse}` | 27 | `\x1b[27m` | 반전 해제 |
| `{/hidden}` | 28 | `\x1b[28m` | 숨김 해제 |
| `{/strikethrough}` | 29 | `\x1b[29m` | 취소선 해제 |

---

## 4. 전경색 (16색)

### Standard (dark) — 소문자

| GenOS 코드 | SGR 코드 | ANSI 이스케이프 | 색상 |
|-----------|----------|----------------|------|
| `{black}` | 30 | `\x1b[30m` | 검정 |
| `{red}` | 31 | `\x1b[31m` | 빨강 |
| `{green}` | 32 | `\x1b[32m` | 초록 |
| `{yellow}` | 33 | `\x1b[33m` | 노랑 (어두운) |
| `{blue}` | 34 | `\x1b[34m` | 파랑 |
| `{magenta}` | 35 | `\x1b[35m` | 자홍 |
| `{cyan}` | 36 | `\x1b[36m` | 청록 |
| `{white}` | 37 | `\x1b[37m` | 흰색 (밝은 회색) |

### Bright — 대문자

| GenOS 코드 | SGR 코드 | ANSI 이스케이프 | 색상 |
|-----------|----------|----------------|------|
| `{BLACK}` | 90 | `\x1b[90m` | 진회색 |
| `{RED}` | 91 | `\x1b[91m` | 밝은 빨강 |
| `{GREEN}` | 92 | `\x1b[92m` | 밝은 초록 |
| `{YELLOW}` | 93 | `\x1b[93m` | 밝은 노랑 |
| `{BLUE}` | 94 | `\x1b[94m` | 밝은 파랑 |
| `{MAGENTA}` | 95 | `\x1b[95m` | 밝은 자홍 |
| `{CYAN}` | 96 | `\x1b[96m` | 밝은 청록 |
| `{WHITE}` | 97 | `\x1b[97m` | 밝은 흰색 |

### 전경색 리셋

| GenOS 코드 | SGR 코드 | ANSI 이스케이프 | 설명 |
|-----------|----------|----------------|------|
| `{/fg}` | 39 | `\x1b[39m` | 기본 전경색으로 복원 |

---

## 5. 배경색 (16색)

### Standard — `bg:소문자`

| GenOS 코드 | SGR 코드 | ANSI 이스케이프 | 색상 |
|-----------|----------|----------------|------|
| `{bg:black}` | 40 | `\x1b[40m` | 검정 배경 |
| `{bg:red}` | 41 | `\x1b[41m` | 빨강 배경 |
| `{bg:green}` | 42 | `\x1b[42m` | 초록 배경 |
| `{bg:yellow}` | 43 | `\x1b[43m` | 노랑 배경 |
| `{bg:blue}` | 44 | `\x1b[44m` | 파랑 배경 |
| `{bg:magenta}` | 45 | `\x1b[45m` | 자홍 배경 |
| `{bg:cyan}` | 46 | `\x1b[46m` | 청록 배경 |
| `{bg:white}` | 47 | `\x1b[47m` | 흰색 배경 |

### Bright — `BG:대문자`

| GenOS 코드 | SGR 코드 | ANSI 이스케이프 | 색상 |
|-----------|----------|----------------|------|
| `{BG:BLACK}` | 100 | `\x1b[100m` | 진회색 배경 |
| `{BG:RED}` | 101 | `\x1b[101m` | 밝은 빨강 배경 |
| `{BG:GREEN}` | 102 | `\x1b[102m` | 밝은 초록 배경 |
| `{BG:YELLOW}` | 103 | `\x1b[103m` | 밝은 노랑 배경 |
| `{BG:BLUE}` | 104 | `\x1b[104m` | 밝은 파랑 배경 |
| `{BG:MAGENTA}` | 105 | `\x1b[105m` | 밝은 자홍 배경 |
| `{BG:CYAN}` | 106 | `\x1b[106m` | 밝은 청록 배경 |
| `{BG:WHITE}` | 107 | `\x1b[107m` | 밝은 흰색 배경 |

### 배경색 리셋

| GenOS 코드 | SGR 코드 | ANSI 이스케이프 | 설명 |
|-----------|----------|----------------|------|
| `{/bg}` | 49 | `\x1b[49m` | 기본 배경색으로 복원 |

---

## 6. 256색 (확장 팔레트)

SGR `38;5;N` (전경) / `48;5;N` (배경) 사용.

### 문법

```
전경: {fg:N}      N = 0~255
배경: {bg:N}      N = 0~255
```

### 팔레트 구조

| 범위 | 용도 | 설명 |
|------|------|------|
| 0-7 | 표준 8색 | black, red, green, yellow, blue, magenta, cyan, white |
| 8-15 | 밝은 8색 | 위 8색의 bright 버전 |
| 16-231 | 216색 큐브 | 6×6×6 RGB 큐브 (R×36 + G×6 + B + 16) |
| 232-255 | 그레이스케일 | 24단계 회색 (232=거의 검정, 255=거의 흰색) |

### 예시

```
{fg:196}        밝은 빨강 (256색 팔레트)
{bg:21}         진한 파랑 배경
{fg:232}        거의 검정 (그레이스케일 시작)
{fg:255}        거의 흰색 (그레이스케일 끝)
{fg:208}        오렌지 (10woongi %^ORANGE%^ 매핑)
```

### ANSI 이스케이프 변환

```
{fg:N}  →  \x1b[38;5;Nm
{bg:N}  →  \x1b[48;5;Nm
```

---

## 7. 24-bit 트루컬러 (RGB)

SGR `38;2;R;G;B` (전경) / `48;2;R;G;B` (배경) 사용.

### 문법

```
전경: {fg:R,G,B}    R,G,B = 0~255
배경: {bg:R,G,B}    R,G,B = 0~255
```

### 예시

```
{fg:255,128,0}     오렌지
{fg:128,0,255}     보라
{bg:0,0,128}       네이비 배경
{fg:255,215,0}     골드
{bg:64,64,64}      진회색 배경
```

### ANSI 이스케이프 변환

```
{fg:R,G,B}  →  \x1b[38;2;R;G;Bm
{bg:R,G,B}  →  \x1b[48;2;R;G;Bm
```

### 256색 vs 트루컬러 구분

파서는 쉼표(`,`) 유무로 구분한다:

```
{fg:196}         → 쉼표 없음 → 256색 (38;5;196)
{fg:255,128,0}   → 쉼표 있음 → 트루컬러 (38;2;255;128;0)
```

---

## 8. 4게임 → GenOS 변환 매핑

### 8.1 tbaMUD (C 매크로 → GenOS)

tbaMUD는 소스 코드에서 C 매크로를 사용하지만, 마이그레이션 출력(SQL/Lua)의 텍스트 데이터에는 `\t(코드)` 형식의 런타임 코드가 사용된다.

| tbaMUD `\t` 코드 | tbaMUD 매크로 | GenOS 코드 |
|-----------------|-------------|-----------|
| `\tn` | `KNRM` | `{reset}` |
| `\tl` | `KBLK` | `{black}` |
| `\tr` | `KRED` | `{red}` |
| `\tg` | `KGRN` | `{green}` |
| `\ty` | `KYEL` | `{yellow}` |
| `\tb` | `KBLU` | `{blue}` |
| `\tm` | `KMAG` | `{magenta}` |
| `\tc` | `KCYN` | `{cyan}` |
| `\tw` | `KWHT` | `{white}` |
| `\tL` | `BBLK` | `{BLACK}` |
| `\tR` | `BRED` | `{RED}` |
| `\tG` | `BGRN` | `{GREEN}` |
| `\tY` | `BYEL` | `{YELLOW}` |
| `\tB` | `BBLU` | `{BLUE}` |
| `\tM` | `BMAG` | `{MAGENTA}` |
| `\tC` | `BCYN` | `{CYAN}` |
| `\tW` | `BWHT` | `{WHITE}` |
| `\tu` | `CUDL` | `{underline}` |
| `\tf` | `CFSH` | `{blink}` |
| `\tv` | `CRVS` | `{reverse}` |
| `\to` | `BKBLK` | `{bg:black}` |
| `\te1` | `BKRED` | `{bg:red}` |
| `\te2` | `BKGRN` | `{bg:green}` |
| `\te3` | `BKYEL` | `{bg:yellow}` |
| `\te4` | `BKBLU` | `{bg:blue}` |
| `\te5` | `BKMAG` | `{bg:magenta}` |
| `\te6` | `BKCYN` | `{bg:cyan}` |
| `\te7` | `BKWHT` | `{bg:white}` |

### 8.2 Simoon (`&X` 코드 → GenOS)

| Simoon 코드 | GenOS 코드 |
|------------|-----------|
| `&r` | `{red}` |
| `&g` | `{green}` |
| `&y` | `{yellow}` |
| `&b` | `{blue}` |
| `&m` | `{magenta}` |
| `&c` | `{cyan}` |
| `&w` | `{white}` |
| `&R` | `{RED}` |
| `&G` | `{GREEN}` |
| `&Y` | `{YELLOW}` |
| `&B` | `{BLUE}` |
| `&M` | `{MAGENTA}` |
| `&C` | `{CYAN}` |
| `&W` | `{WHITE}` |
| `[=NF` | `{fg:N}` (N을 16색 또는 256색으로 매핑) |

### 8.3 3eyes (`[=NF`/`{한글}` → GenOS)

| 3eyes 코드 | GenOS 코드 | 비고 |
|-----------|-----------|------|
| `[=07F` | `{white}` | 기본 전경 |
| `[=04F` | `{blue}` | |
| `[=11F` | `{CYAN}` | 밝은 청록 |
| `[=0G` | `{bg:black}` | 기본 배경 |
| `{붉...}` | `{red}` | 한글 색이름 |
| `{초...}` | `{green}` | |
| `{노...}` | `{yellow}` | |
| `{남...}` | `{blue}` | |
| `{분...}` | `{magenta}` | |
| `}` (리셋) | `{reset}` | |

### 8.4 10woongi (`%^NAME%^` → GenOS)

| 10woongi 코드 | GenOS 코드 |
|-------------|-----------|
| `%^BLACK%^` | `{black}` |
| `%^RED%^` | `{red}` |
| `%^GREEN%^` | `{green}` |
| `%^YELLOW%^` | `{yellow}` |
| `%^BLUE%^` | `{blue}` |
| `%^MAGENTA%^` | `{magenta}` |
| `%^CYAN%^` | `{cyan}` |
| `%^WHITE%^` | `{white}` |
| `%^BBLACK%^` | `{BLACK}` |
| `%^BRED%^` | `{RED}` |
| `%^BGREEN%^` | `{GREEN}` |
| `%^BYELLOW%^` | `{YELLOW}` |
| `%^BBLUE%^` | `{BLUE}` |
| `%^BMAGENTA%^` | `{MAGENTA}` |
| `%^BCYAN%^` | `{CYAN}` |
| `%^BWHITE%^` | `{WHITE}` |
| `%^ORANGE%^` | `{fg:208}` |
| `%^BORANGE%^` | `{fg:214}` |
| `%^BOLD%^` | `{bold}` |
| `%^RESET%^` | `{reset}` |
| `%^B_BLACK%^` | `{bg:black}` |
| `%^B_RED%^` | `{bg:red}` |
| `%^B_GREEN%^` | `{bg:green}` |
| `%^B_YELLOW%^` | `{bg:yellow}` |
| `%^B_BLUE%^` | `{bg:blue}` |
| `%^B_MAGENTA%^` | `{bg:magenta}` |
| `%^B_CYAN%^` | `{bg:cyan}` |
| `%^B_WHITE%^` | `{bg:white}` |

---

## 9. 엔진 구현: GenOS → ANSI 변환기

`core/ansi.py` — 모든 게임이 공유하는 단일 변환기.

```python
"""GenOS ANSI 컬러 포맷 → ANSI 이스케이프 시퀀스 변환기"""
import re

# 고정 매핑 (리셋 + 포맷 + 16색 전경/배경)
_FIXED: dict[str, str] = {
    # 리셋
    "reset": "\x1b[0m",
    # 텍스트 포맷
    "bold": "\x1b[1m", "dim": "\x1b[2m", "italic": "\x1b[3m",
    "underline": "\x1b[4m", "blink": "\x1b[5m", "rapid_blink": "\x1b[6m",
    "reverse": "\x1b[7m", "hidden": "\x1b[8m", "strikethrough": "\x1b[9m",
    # 포맷 해제
    "/bold": "\x1b[22m", "/dim": "\x1b[22m", "/italic": "\x1b[23m",
    "/underline": "\x1b[24m", "/blink": "\x1b[25m",
    "/reverse": "\x1b[27m", "/hidden": "\x1b[28m", "/strikethrough": "\x1b[29m",
    # 전경 리셋 / 배경 리셋
    "/fg": "\x1b[39m", "/bg": "\x1b[49m",
    # 전경 standard (dark)
    "black": "\x1b[30m", "red": "\x1b[31m", "green": "\x1b[32m",
    "yellow": "\x1b[33m", "blue": "\x1b[34m", "magenta": "\x1b[35m",
    "cyan": "\x1b[36m", "white": "\x1b[37m",
    # 전경 bright
    "BLACK": "\x1b[90m", "RED": "\x1b[91m", "GREEN": "\x1b[92m",
    "YELLOW": "\x1b[93m", "BLUE": "\x1b[94m", "MAGENTA": "\x1b[95m",
    "CYAN": "\x1b[96m", "WHITE": "\x1b[97m",
    # 배경 standard
    "bg:black": "\x1b[40m", "bg:red": "\x1b[41m", "bg:green": "\x1b[42m",
    "bg:yellow": "\x1b[43m", "bg:blue": "\x1b[44m", "bg:magenta": "\x1b[45m",
    "bg:cyan": "\x1b[46m", "bg:white": "\x1b[47m",
    # 배경 bright
    "BG:BLACK": "\x1b[100m", "BG:RED": "\x1b[101m", "BG:GREEN": "\x1b[102m",
    "BG:YELLOW": "\x1b[103m", "BG:BLUE": "\x1b[104m", "BG:MAGENTA": "\x1b[105m",
    "BG:CYAN": "\x1b[106m", "BG:WHITE": "\x1b[107m",
}

_PATTERN = re.compile(r"\{([^}]+)\}")


def to_ansi(text: str) -> str:
    """GenOS 포맷 → ANSI 이스케이프 시퀀스 변환"""
    def _replace(m: re.Match) -> str:
        code = m.group(1)
        # 1. 고정 매핑 조회
        if code in _FIXED:
            return _FIXED[code]
        # 2. 동적 매핑: {fg:...} / {bg:...}
        if ":" in code:
            prefix, value = code.split(":", 1)
            if prefix in ("fg", "bg"):
                sgr = "38" if prefix == "fg" else "48"
                if "," in value:
                    # 24-bit 트루컬러: {fg:R,G,B}
                    return f"\x1b[{sgr};2;{value.replace(',', ';')}m"
                else:
                    # 256색: {fg:N}
                    return f"\x1b[{sgr};5;{value}m"
        # 3. 매칭 실패 → 원본 유지
        return m.group(0)

    return _PATTERN.sub(_replace, text)


def strip(text: str) -> str:
    """GenOS 컬러 코드 제거 (비컬러 클라이언트용)"""
    return _PATTERN.sub("", text)


def strip_ansi(text: str) -> str:
    """ANSI 이스케이프 시퀀스 제거"""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)
```

---

## 10. 마이그레이션 도구 구현: 원본 → GenOS 변환기

각 어댑터에서 텍스트 필드를 GenOS 포맷으로 변환하는 함수:

```python
# 마이그레이션 도구에서 사용 (개념 코드)

def convert_tbamud_colors(text: str) -> str:
    """tbaMUD \\t 코드 → GenOS 포맷"""
    TBAMUD_MAP = {
        "\\tn": "{reset}", "\\tr": "{red}", "\\tR": "{RED}",
        "\\tg": "{green}", "\\tG": "{GREEN}", "\\tb": "{blue}",
        "\\tB": "{BLUE}", "\\ty": "{yellow}", "\\tY": "{YELLOW}",
        "\\tm": "{magenta}", "\\tM": "{MAGENTA}", "\\tc": "{cyan}",
        "\\tC": "{CYAN}", "\\tw": "{white}", "\\tW": "{WHITE}",
        "\\tl": "{black}", "\\tL": "{BLACK}",
        "\\tu": "{underline}", "\\tf": "{blink}", "\\tv": "{reverse}",
        "\\to": "{bg:black}",
    }
    for old, new in TBAMUD_MAP.items():
        text = text.replace(old, new)
    return text

def convert_simoon_colors(text: str) -> str:
    """Simoon &X 코드 → GenOS 포맷"""
    SIMOON_MAP = {
        "&r": "{red}", "&R": "{RED}", "&g": "{green}", "&G": "{GREEN}",
        "&b": "{blue}", "&B": "{BLUE}", "&y": "{yellow}", "&Y": "{YELLOW}",
        "&m": "{magenta}", "&M": "{MAGENTA}", "&c": "{cyan}", "&C": "{CYAN}",
        "&w": "{white}", "&W": "{WHITE}",
    }
    for old, new in SIMOON_MAP.items():
        text = text.replace(old, new)
    return text

def convert_3eyes_colors(text: str) -> str:
    """3eyes [=NF / {한글} 코드 → GenOS 포맷"""
    # [=NF 형식 변환
    import re
    EYES_FG = {7: "{white}", 4: "{blue}", 11: "{CYAN}", 0: "{black}"}
    def _replace_fg(m):
        n = int(m.group(1))
        return EYES_FG.get(n, f"{{fg:{n}}}")
    text = re.sub(r"\x1b\[=(\d+)F", _replace_fg, text)
    # {한글} 형식 변환
    KR_MAP = {"붉": "{red}", "초": "{green}", "노": "{yellow}",
              "남": "{blue}", "분": "{magenta}", "외": "{cyan}"}
    for kr, genos in KR_MAP.items():
        text = text.replace(f"{{{kr}", genos)
    return text

def convert_10woongi_colors(text: str) -> str:
    """10woongi %^NAME%^ 코드 → GenOS 포맷"""
    import re
    WOONGI_MAP = {
        "BLACK": "{black}", "RED": "{red}", "GREEN": "{green}",
        "YELLOW": "{yellow}", "BLUE": "{blue}", "MAGENTA": "{magenta}",
        "CYAN": "{cyan}", "WHITE": "{white}",
        "BBLACK": "{BLACK}", "BRED": "{RED}", "BGREEN": "{GREEN}",
        "BYELLOW": "{YELLOW}", "BBLUE": "{BLUE}", "BMAGENTA": "{MAGENTA}",
        "BCYAN": "{CYAN}", "BWHITE": "{WHITE}",
        "ORANGE": "{fg:208}", "BORANGE": "{fg:214}",
        "BOLD": "{bold}", "RESET": "{reset}",
        "B_BLACK": "{bg:black}", "B_RED": "{bg:red}", "B_GREEN": "{bg:green}",
        "B_YELLOW": "{bg:yellow}", "B_BLUE": "{bg:blue}",
        "B_MAGENTA": "{bg:magenta}", "B_CYAN": "{bg:cyan}", "B_WHITE": "{bg:white}",
    }
    def _replace(m):
        name = m.group(1)
        return WOONGI_MAP.get(name, m.group(0))
    return re.sub(r"%\^([A-Z_]+)%\^", _replace, text)
```

---

## 11. 클라이언트 호환성

### Telnet 클라이언트

| 클라이언트 | 16색 | 256색 | 트루컬러 | 비고 |
|-----------|------|-------|---------|------|
| MUSHclient | O | O | X | Windows 전용 |
| Mudlet | O | O | O | 크로스 플랫폼 |
| TinTin++ | O | O | O | 리눅스/macOS |
| PuTTY | O | △ | X | 설정 필요 |
| zMUD/cMUD | O | X | X | 레거시 |

### 비컬러 클라이언트 대응

ANSI를 지원하지 않는 클라이언트에는 `strip()` 함수로 GenOS 코드를 제거한 순수 텍스트를 전송한다. 세션 생성 시 ANSI 지원 여부를 확인하고 플래그로 저장:

```python
if session.supports_ansi:
    output = to_ansi(text)
else:
    output = strip(text)
```

---

## 12. 예시: 실제 변환

### tbaMUD 방 묘사

```
원본:   \tCThe Temple of Midgaard\tn\r\nYou are standing in the \tYholy temple\tn.
GenOS:  {CYAN}The Temple of Midgaard{reset}\r\nYou are standing in the {YELLOW}holy temple{reset}.
출력:   \x1b[96mThe Temple of Midgaard\x1b[0m\r\nYou are standing in the \x1b[93mholy temple\x1b[0m.
```

### Simoon 전투 메시지

```
원본:   &R고블린&w이 &Y불꽃&w으로 공격합니다!
GenOS:  {RED}고블린{white}이 {YELLOW}불꽃{white}으로 공격합니다!
출력:   \x1b[91m고블린\x1b[37m이 \x1b[93m불꽃\x1b[37m으로 공격합니다!
```

### 10woongi 시스템 메시지

```
원본:   %^BRED%^[경고]%^RESET%^ %^CYAN%^서버가 곧 재시작됩니다.%^RESET%^
GenOS:  {RED}[경고]{reset} {cyan}서버가 곧 재시작됩니다.{reset}
출력:   \x1b[91m[경고]\x1b[0m \x1b[36m서버가 곧 재시작됩니다.\x1b[0m
```

---

**문서 버전**: 1.0
**최종 업데이트**: 2026-02-10 — 초판 작성. GenOS 공통 ANSI 포맷 정의, 4게임 변환 매핑, 엔진/마이그레이션 구현 가이드
