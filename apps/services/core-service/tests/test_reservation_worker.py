from datetime import date
from decimal import Decimal
from unittest.mock import patch

from app.workers.reservation_worker import (
    periodos_se_sobrepoem,
    simular_pagamento,
)


def test_periodos_com_noites_em_comum_sobrepoem():
    assert periodos_se_sobrepoem(
        date(2026, 11, 10), date(2026, 11, 15),
        date(2026, 11, 14), date(2026, 11, 18),
    )


def test_checkout_e_checkin_no_mesmo_dia_nao_sobrepoem():
    assert not periodos_se_sobrepoem(
        date(2026, 11, 10), date(2026, 11, 15),
        date(2026, 11, 15), date(2026, 11, 18),
    )


def test_periodos_sem_intersecao_nao_sobrepoem():
    assert not periodos_se_sobrepoem(
        date(2026, 11, 10), date(2026, 11, 12),
        date(2026, 11, 13), date(2026, 11, 16),
    )


def test_pagamento_aprovado():
    with patch("app.workers.reservation_worker.random.random", return_value=0.25):
        assert simular_pagamento(Decimal("350.00")) is True


def test_pagamento_recusado():
    with patch("app.workers.reservation_worker.random.random", return_value=0.95):
        assert simular_pagamento(Decimal("350.00")) is False


def test_pagamento_recusa_valor_invalido():
    assert simular_pagamento(Decimal("0.00")) is False
    assert simular_pagamento(Decimal("-10.00")) is False
