user_vector = {
    "gender": {
        "M": 1.0,
        "F": 0.0
    },
    "age": 22,
    "kdc": {
        "문학": 0.6,
        "사회과학": 0.4
    },
    "genre": {
        "한국소설": 0.7,
        "에세이": 0.3
    }
}


def gender_score(user_gender, book_gender_stats):
    if user_gender == "any":
        return 0.5
    return book_gender_stats.get(user_gender, 0)


def recommendation_score(user, book):
    kdc_score = user["kdc"].get(book["kdc"], 0)
    genre_score = user["genre"].get(book["genre"], 0)
    age_match = 1 if book["from_age"] <= user["age"] <= book["to_age"] else 0
    gender_match = book["gender_ratio"].get(user["gender"], 0.5)

    score = (
        0.35 * kdc_score +
        0.30 * genre_score +
        0.20 * age_match +
        0.15 * gender_match
    )
    return score

selected_genres = ["한국소설", "에세이", "인문"]

weight = 1 / len(selected_genres)
genre_vector = {g: weight for g in selected_genres}
