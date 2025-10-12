# config.py

BASE_URL = "https://www.amazon.in/ASUS-3050-4GB-Keyboard-Graphite-FA506NCG-HN199W/dp/B0FM3C4L2F/?_encoding=UTF8&pd_rd_w=Qptth&content-id=amzn1.sym.aea64848-3ab9-4698-b7eb-c51ed2480b56&pf_rd_p=aea64848-3ab9-4698-b7eb-c51ed2480b56&pf_rd_r=CWSQR61Y5G9M17YHG2RD&pd_rd_wg=STWeY&pd_rd_r=43033c74-df5b-4e09-a4f0-87a5adbf4a75&ref_=pd_hp_d_btf_CEPC_Smartwatches&th=1"
CSS_SELECTOR = "[class^='reviewsMedley']"
REQUIRED_KEYS = [
    "user",
    "review_date",
    "rating",
    "review_text"
]
