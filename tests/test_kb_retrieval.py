from agents.kb_retrieval import retrieve


def test_retrieve_hit_return_policy():
    r = retrieve("退货要几天")
    assert not r.is_empty
    assert any(h.entry["id"] == "faq-return-001" for h in r.hits)
    assert r.hits[0].score >= 0.7


def test_retrieve_hit_invoice():
    r = retrieve("电子发票怎么开")
    assert not r.is_empty
    assert any(h.entry["id"] == "faq-invoice-001" for h in r.hits)


def test_retrieve_hit_member_synonym():
    r = retrieve("vip 积分能翻倍吗")
    assert not r.is_empty
    assert any(h.entry["id"] == "faq-member-001" for h in r.hits)


def test_retrieve_empty_unknown_topic():
    r = retrieve("暗物质保修期多久")
    assert r.is_empty
    assert r.max_score < r.threshold


def test_retrieve_respects_max_chunks():
    r = retrieve("会员 积分 优惠券 支付")
    assert len(r.hits) <= 3
