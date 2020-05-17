from lxml import etree

import geocoder
import requests

from bs4 import BeautifulSoup
from pykml.factory import KML_ElementMaker as KML
from pykml.util import format_xml_with_cdata

response = requests.get("https://koa.com/campgrounds/")
soup = BeautifulSoup(response.content, "html.parser")

links = soup.select("a[href^='/campgrounds/']")

folder = KML.Folder()

for link in links:
    print(link.attrs["href"])
    response = requests.get("https://koa.com" + link.attrs["href"])

    soup = BeautifulSoup(response.content, "html.parser")

    try:
        rating = (
            soup.select_one("a[href='reviews/']").span.attrs["class"][0].split("-")[-1]
        )

        if "half" in rating:
            rating = int(rating[0]) + 0.5
        else:
            rating = int(rating[0])
    except AttributeError:
        rating = "No Reviews"

    name = soup.select_one(".mt-0").text
    try:
        alert_msg = soup.select_one(
            "#modal-emergency > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1)"
        ).p.text
    except AttributeError:
        alert_msg = "None"
    reserve_phone = soup.select_one(
        "div.col-sm-6:nth-child(1) > div:nth-child(2) > a:nth-child(2)"
    ).text
    info_phone = soup.select_one(
        "div.col-sm-6:nth-child(1) > div:nth-child(3) > a:nth-child(2)"
    ).text
    email = (
        soup.select_one("a.gtm-mailto-click:nth-child(1)").attrs["href"].split(":")[1]
    )
    try:
        rv_checkout_checkin = soup.select_one(
            "#checkInTimes > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > p:nth-child(2)"
        ).text
    except AttributeError:
        rv_checkout_checkin = "N/A"
    address_1 = soup.select_one(
        "div.col-sm-6:nth-child(1) > div:nth-child(4) > b:nth-child(1)"
    ).text
    address_2 = soup.select_one(
        "div.col-sm-6:nth-child(1) > div:nth-child(5) > b:nth-child(1)"
    ).text

    description = """
<a href="https://koa.com{link_href}">Info Page</a><br>
<b>Alert Message:</b> {alert_msg}<br>
<b>Reserve Phone:</b> {reserve_phone}<br>
<b>Info Phone:</b> {info_phone}<br>
<b>Email:</b> {email}<br>
Checkout Hours:</b> {rv_checkout_checkin}<br>
<b>Address:</b> {address_1}<br>
{address_2}<br>
<b>Rating:</b> {rating}
""".format(
        link_href=link.attrs["href"],
        alert_msg=alert_msg,
        reserve_phone=reserve_phone,
        info_phone=info_phone,
        email=email,
        rv_checkout_checkin=rv_checkout_checkin,
        address_1=address_1,
        address_2=address_2,
        rating=rating,
    )

    # note: this is a free and simple geocoder but not the most accurate
    # google might be best but costs $$
    geocode_result = geocoder.arcgis(", ".join([address_1, address_2]))
    latlng_str = ",".join([str(_) for _ in geocode_result.current_result.latlng[::-1]])
    placemark = KML.Placemark(
        KML.name(name),
        KML.description(description),
        KML.Point(KML.coordinates(latlng_str),),
    )
    folder.append(placemark)

with open("koa-campgrounds.kml", "w") as fh:
    fh.write(
        etree.tostring(
            format_xml_with_cdata(folder),
            method="xml",
            encoding="unicode",
            pretty_print=True,
        )
    )
