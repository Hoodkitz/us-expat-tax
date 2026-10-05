import pytest

from app.modules.submission_saga import (
    create_liability_waiver,
    TollgateError,
    SubmissionSagaState,
    SubmissionState,
    SagaError,
    ElsterSubmissionSaga,
    _mock_verify_totp,
)

SECRET = b"test-server-secret"


def _valid_totp(user_id: str) -> str:
    import time
    import hmac
    import hashlib

    window = int(time.time() // 30)
    return hmac.new(SECRET, f"{user_id}:{window}".encode(), hashlib.sha256).hexdigest()[:6]


def test_tollgate_blocks_wrong_totp():
    with pytest.raises(TollgateError):
        create_liability_waiver("user-1", "000000", SECRET)


def test_tollgate_accepts_valid_totp_and_signs_record():
    code = _valid_totp("user-1")
    record = create_liability_waiver("user-1", code, SECRET)
    assert record.totp_verified is True
    assert len(record.signature) == 64  # sha256 hex
    assert record.waiver_text_hash


def test_unlock_us_forms_blocked_before_transferticket():
    saga = ElsterSubmissionSaga(erica_client=None)
    state = SubmissionSagaState()
    with pytest.raises(SagaError):
        saga.unlock_us_forms(state)


def test_unlock_us_forms_succeeds_after_transferticket():
    saga = ElsterSubmissionSaga(erica_client=None)
    state = SubmissionSagaState()
    state.transition(SubmissionState.ELSTER_TRANSFERTICKET_RECEIVED, "test")
    saga.unlock_us_forms(state)
    assert state.state == SubmissionState.US_FORMS_GENERATED
