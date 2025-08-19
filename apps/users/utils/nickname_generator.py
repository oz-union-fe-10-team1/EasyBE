# apps/users/utils/nickname_generator.py
import random
from typing import List


class NicknameGenerator:
    """랜덤 닉네임 생성기"""

    # 자연스럽게 이어지는 형용사 목록
    ADJECTIVES: List[str] = [
        "몽글몽글",
        "보들보들",
        "말랑말랑",
        "폭신폭신",
        "반짝반짝",
        "토실토실",
        "동글동글",
        "쫀득쫀득",
        "촉촉하게",
        "향긋하게",
        "깔끔하게",
        "산뜻하게",
        "상큼하게",
        "부드럽게",
        "따끈따끈",
        "시원시원",
        "맑게",
        "순하게",
        "특별하게",
        "행복하게",
        "달콤달콤",
        "새콤새콤",
        "짭짤하게",
        "쫄깃쫄깃",
        "바삭바삭",
        "부들부들",
        "물렁물렁",
        "탱글탱글",
        "복슬복슬",
        "푸딩하게",
        "젤리처럼",
        "솜털처럼",
        "포근하게",
        "아늑하게",
        "조심조심",
        "살살",
        "예쁘게",
        "깜찍",
        "사랑스럽게",
        "귀엽게",
    ]

    # 귀여운 동사 목록
    VERBS: List[str] = [
        "뛰어노는",
        "춤추는",
        "노래하는",
        "웃고있는",
        "잠자는",
        "꿈꾸는",
        "산책하는",
        "뒹굴거리는",
        "기지개켜는",
        "하품하는",
        "윙크하는",
        "방긋웃는",
        "토닥토닥",
        "살랑살랑",
        "팔락팔락",
        "깡충깡충",
        "데굴데굴",
        "통통튀는",
        "폴짝폴짝",
        "슬금슬금",
        "아장아장",
        "종종걸음",
        "까르르웃는",
        "꼬물꼬물",
        "달려가는",
    ]

    # 귀여운 동물/캐릭터 명사 목록
    NOUNS: List[str] = [
        "햄스터",
        "다람쥐",
        "토끼",
        "고양이",
        "강아지",
        "펭귄",
        "코알라",
        "판다",
        "알파카",
        "미어캣",
        "오리",
        "병아리",
        "부엉이",
        "참새",
        "리스",
        "여우",
        "곰돌이",
        "사슴",
        "양",
        "돼지",
        "문어",
        "해파리",
        "별가사리",
        "조개",
        "새우",
        "딸기",
        "복숭아",
        "포도",
        "수박",
        "바나나",
        "도넛",
        "케이크",
        "마카롱",
        "푸딩",
        "젤리",
        "구름",
        "별님",
        "달님",
        "꽃잎",
        "나뭇잎",
    ]

    @classmethod
    def generate_random_nickname(cls) -> str:
        """형용사 + 동사 + 명사 조합으로 랜덤 닉네임 생성"""
        adjective = random.choice(cls.ADJECTIVES)
        verb = random.choice(cls.VERBS)
        noun = random.choice(cls.NOUNS)

        return f"{adjective}{verb}{noun}"

    @classmethod
    def generate_unique_nickname(cls, user_model) -> str:
        """단계적으로 유니크한 닉네임 생성"""
        max_attempts = 50  # 각 단계별 최대 시도 횟수

        # 1단계: 형용사 or 동사 + 명사 (2단어)
        for _ in range(max_attempts):
            # 형용사 또는 동사 중 랜덤 선택
            modifier = random.choice(cls.ADJECTIVES + cls.VERBS)
            noun = random.choice(cls.NOUNS)
            nickname = f"{modifier}{noun}"

            if not user_model.objects.filter(nickname=nickname).exists():
                return nickname

        # 2단계: 형용사 + 동사 + 명사 (3단어)
        for _ in range(max_attempts):
            adjective = random.choice(cls.ADJECTIVES)
            verb = random.choice(cls.VERBS)
            noun = random.choice(cls.NOUNS)
            nickname = f"{adjective}{verb}{noun}"

            if not user_model.objects.filter(nickname=nickname).exists():
                return nickname

        # 3단계: 최후의 수단으로 숫자 추가
        import time

        timestamp = str(int(time.time()))[-3:]  # 마지막 3자리
        base_nickname = cls.generate_random_nickname()
        return f"{base_nickname}{timestamp}"
