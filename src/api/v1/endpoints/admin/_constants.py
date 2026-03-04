"""
Admin 엔드포인트 공유 상수.

상태 메타 정보와 역할 레이블을 중앙화하여
모든 admin 서브 모듈이 일관된 값을 사용한다.
"""

STATUS_META: dict[str, dict] = {
    "접수됨":   {"color": "#86BBD8", "bg": "rgba(134,187,216,0.14)", "emoji": "📥"},
    "수거예정": {"color": "#FFD166", "bg": "rgba(255,209,102,0.14)", "emoji": "🚚"},
    "판매중":   {"color": "#F26419", "bg": "rgba(242,100,25,0.14)",  "emoji": "🔥"},
    "정산완료": {"color": "#48C78E", "bg": "rgba(72,199,142,0.14)",  "emoji": "✅"},
    "취소됨":   {"color": "rgba(255,255,255,0.35)", "bg": "rgba(255,255,255,0.06)", "emoji": "❌"},
}

ROLE_LABELS: dict[str, str] = {
    "super_admin": "슈퍼관리자",
    "operator":    "운영자",
    "settler":     "정산담당",
    "guest":       "Guest",
}

VALID_ROLES = frozenset(ROLE_LABELS.keys())
