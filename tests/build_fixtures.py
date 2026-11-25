#!/usr/bin/env python3
import json, os, re
from urllib.parse import urlparse
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
for d in ("week1", "week2", "our-pages"):
    os.makedirs(os.path.join(F, d), exist_ok=True)
def slug(u):
    p = urlparse(u); return re.sub(r"[^A-Za-z0-9.]+", "_", (p.netloc + p.path).strip("/")) + ".html"
U = {"acme": "https://acme.example.com/pricing", "beta": "https://beta.example.com/plans", "gamma": "https://gamma.example.com/pricing",
     "delta": "https://delta.example.com/pricing", "echo": "https://echo.example.com/pricing", "fox": "https://fox.example.com/pricing"}
page = lambda body: "<html><head><style>.x{}</style><script>var price='$1';</script></head><body>%s</body></html>" % body
W1 = {"acme": "<h2>Pro</h2><p>$29 per month, billed monthly.</p>",
      "beta": "<h2>Free</h2><ul><li>Up to 500&nbsp;contacts</li></ul>",
      "gamma": "<h2>Starter</h2><p>$99 per month</p>",
      "delta": "<h2>Plans</h2><p>Every plan has a 14-day free trial.</p>",
      "echo": "<h2>Annual</h2><p><s>$20</s> now $30 per month</p>"}
W2 = dict(W1, acme="<h2>Pro</h2><p>$35 per month, billed monthly.</p>", delta="<h2>Plans</h2><p>Talk to sales for a demo.</p>")
for wk, W in (("week1", W1), ("week2", W2)):
    for k, body in W.items():
        open(os.path.join(F, wk, slug(U[k])), "w").write(page(body))
facts = [
 {"id": "acme-pro-price", "entity": "Acme CRM Pro plan", "attribute": "price", "value": "$29", "keywords": ["Pro"], "source_url": U["acme"], "our_page": "our-pages/acme-review.md", "priority": "high"},
 {"id": "beta-free-limit", "entity": "Beta Mail Free plan", "attribute": "contact limit", "value": "500 contacts", "keywords": ["Free"], "source_url": U["beta"], "our_page": "our-pages/beta-review.md"},
 {"id": "gamma-starter-price", "entity": "Gamma Starter plan", "attribute": "price", "value": "$9", "keywords": ["Starter"], "source_url": U["gamma"]},
 {"id": "delta-trial", "entity": "Delta Free trial", "attribute": "trial length", "value": "14-day free trial", "keywords": ["trial"], "source_url": U["delta"], "priority": "low"},
 {"id": "echo-annual-price", "entity": "Echo Annual plan", "attribute": "price", "value": "$20", "keywords": ["Annual"], "source_url": U["echo"]},
 {"id": "fox-price", "entity": "Fox Basic plan", "attribute": "price", "value": "$5", "keywords": ["Basic"], "source_url": U["fox"]},
]
json.dump(facts, open(os.path.join(F, "facts.json"), "w"), indent=2)
open(os.path.join(F, "our-pages", "acme-review.md"), "w").write("# Acme CRM review\nThe Pro plan costs $29 a month.\n")
open(os.path.join(F, "our-pages", "beta-review.md"), "w").write("# Beta Mail review\nThe free plan is generous.\n")
