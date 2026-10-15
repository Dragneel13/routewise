from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    SimpleDocTemplate,
)

from app.models.trip import Trip


def generate_trip_pdf(
    trip: Trip,
    stops: list,
    legs: list,
    weather: dict,
    budget: dict,
) -> bytes:
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"RouteWise - {trip.name}",
        author="RouteWise",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RouteWiseTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "RouteWiseSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=18,
    )

    heading_style = ParagraphStyle(
        "RouteWiseHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "RouteWiseNormal",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
    )

    story = []
    story.append(Paragraph("RouteWise", title_style))
    story.append(
        Paragraph(
            "Smart Pune Trip Planner",
            subtitle_style,
        )
    )

    story.append(
        Paragraph(
            trip.name,
            styles["Heading1"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Starting location:</b> {trip.start_location}",
            normal_style,
        )
    )

    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Budget Summary",
            heading_style,
        )
    )

    budget_data = [
        ["Item", "Amount"],
        ["Budget", f"₹{budget['budget']:.2f}"],
        [
            "Transport",
            f"₹{budget['total_transport_cost']:.2f}",
        ],
        [
            "Entry fees",
            f"₹{budget['total_entry_cost']:.2f}",
        ],
        [
            "Food estimate",
            f"₹{budget['total_food_cost']:.2f}",
        ],
        [
            "Buffer",
            f"₹{budget['buffer_cost']:.2f}",
        ],
        [
            "Estimated total",
            f"₹{budget['estimated_total']:.2f}",
        ],
        [
            "Remaining",
            f"₹{budget['remaining_budget']:.2f}",
        ],
        [
            "Budget used",
            f"{budget['budget_used_percent']:.1f}%",
        ],
        [
            "Status",
            budget["budget_status"],
        ],
    ]

    budget_table = Table(
        budget_data,
        colWidths=[70 * mm, 90 * mm],
    )

    budget_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1f2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(budget_table)
    story.append(
        Paragraph(
            "Weather",
            heading_style,
        )
    )

    if weather.get("available"):
        weather_text = (
            f"<b>Pune:</b> {weather.get('description', 'Unknown')}<br/>"
            f"<b>Temperature:</b> "
            f"{weather.get('temperature_c', 'N/A')}°C<br/>"
            f"<b>Humidity:</b> "
            f"{weather.get('humidity_percent', 'N/A')}%<br/>"
            f"<b>Precipitation:</b> "
            f"{weather.get('precipitation_mm', 'N/A')} mm<br/>"
            f"<b>Wind:</b> "
            f"{weather.get('wind_speed_kmh', 'N/A')} km/h<br/>"
            f"<b>Weather risk:</b> "
            f"{weather.get('weather_risk', 'N/A')}<br/>"
            f"<b>Recommendation:</b> "
            f"{weather.get('recommendation', 'N/A')}"
        )
    else:
        weather_text = "Weather information is currently unavailable."

    story.append(
        Paragraph(
            weather_text,
            normal_style,
        )
    )
    story.append(
        Paragraph(
            "Itinerary",
            heading_style,
        )
    )

    itinerary_data = [
        [
            "#",
            "Place",
            "Area",
            "Duration",
            "Entry",
        ]
    ]

    for index, stop in enumerate(stops, start=1):
        itinerary_data.append(
            [
                str(index),
                stop["poi_name"],
                stop["area"],
                f"{stop['duration_minutes']} min",
                f"₹{stop['entry_cost']:.2f}",
            ]
        )

    if len(itinerary_data) > 1:
        itinerary_table = Table(
            itinerary_data,
            colWidths=[
                10 * mm,
                55 * mm,
                35 * mm,
                30 * mm,
                25 * mm,
            ],
            repeatRows=1,
        )

        itinerary_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1f2937"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(itinerary_table)
    else:
        story.append(
            Paragraph(
                "No itinerary stops have been added yet.",
                normal_style,
            )
        )
    story.append(
        Paragraph(
            "Transport Plan",
            heading_style,
        )
    )

    if legs:
        transport_data = [
            [
                "From",
                "To",
                "Mode",
                "Duration",
                "Walk",
                "Fare",
            ]
        ]

        stop_names = {
            stop["stop_id"]: stop["poi_name"]
            for stop in stops
        }

        for leg in legs:
            transport_data.append(
                [
                    stop_names.get(
                        leg.from_stop_id,
                        str(leg.from_stop_id),
                    ),
                    stop_names.get(
                        leg.to_stop_id,
                        str(leg.to_stop_id),
                    ),
                    leg.mode,
                    f"{leg.duration_minutes} min",
                    f"{leg.walking_minutes} min",
                    f"₹{leg.fare:.2f}",
                ]
            )

        transport_table = Table(
            transport_data,
            colWidths=[
                35 * mm,
                35 * mm,
                25 * mm,
                25 * mm,
                20 * mm,
                20 * mm,
            ],
            repeatRows=1,
        )

        transport_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1f2937"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(transport_table)
    else:
        story.append(
            Paragraph(
                "No transport legs have been selected yet.",
                normal_style,
            )
        )

    story.append(Spacer(1, 18))

    story.append(
        Paragraph(
            "Generated by RouteWise — Pune Smart Trip Planner",
            subtitle_style,
        )
    )

    document.build(story)

    return buffer.getvalue()