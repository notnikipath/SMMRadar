from shared.smmradar_common import Role, has_permission, sign_token, verify_token


def test_sign_and_verify_token() -> None:
    token = sign_token({"sub": "user-1", "role": Role.MANAGER.value}, "secret", exp_minutes=10)
    payload = verify_token(token, "secret")
    assert payload is not None
    assert payload["sub"] == "user-1"



def test_permission_matrix() -> None:
    assert has_permission(Role.MANAGER, "notification:send") is True
    assert has_permission(Role.ANALYST, "notification:send") is False
