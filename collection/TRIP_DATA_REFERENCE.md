# Trip Data Reference

This document shows the consistent data structure used across the Bruno API collection.

## Trip: Japan Adventure 2025

**Trip Details:**
- Name: "Japan Adventure 2025"
- Dates: January 1-14, 2025
- Start: 1735689600 (Jan 1, 2025 00:00:00 UTC)
- End: 1736899200 (Jan 14, 2025 00:00:00 UTC)
- Timezone: Asia/Tokyo
- Locations: Tokyo, Kyoto, Osaka
- Trip Type: multi_city
- Status: planning
- Budget: $5,000 USD

## Trip Days

### Day 1 - January 1, 2025 (Arrival)
- Date: 2025-01-01
- Day Number: 1
- Type: transit
- Place: Narita Airport → Shinjuku
- Activities: Arrival, hotel check-in, light exploration

### Day 3 - January 3, 2025 (Tokyo Sightseeing)
- Date: 2025-01-03
- Day Number: 3
- Type: sightseeing
- Title: "Exploring Tokyo"
- Place: Shibuya & Harajuku
- Accommodation: Park Hyatt Tokyo
  - Check-in: 1735912800 (Jan 3, 2025 14:00 JST)
  - Check-out: 1735999200 (Jan 4, 2025 11:00 JST)
  - Confirmation: PH2025010203

**Activities:**
1. **Meiji Shrine Visit** (09:00, 2h)
   - Free entry
   - Location: 1-1 Yoyogikamizonocho, Shibuya City, Tokyo

2. **Shibuya Crossing & Shopping** (12:00, 3h)
   - Free
   - Location: Shibuya Scramble Crossing, Tokyo

3. **teamLab Borderless** (16:00, 2.5h)
   - Cost: ¥3,800
   - Location: Azabudai Hills, Minato City, Tokyo
   - Confirmation: TLB20250103
   - Booking required

**Bookings:**
- **Sukiyabashi Jiro** (Dinner, 19:00)
  - Cost: ¥40,000
  - Confirmation: JIRO20250103
  - Location: Tsukamoto Sogyo Building B1F, 2-15 Ginza 4-chome, Chuo-ku, Tokyo
  - Contact: +81-3-3535-3600

### Day 5 - January 5, 2025 (Kyoto Day Trip)
- Date: 2025-01-05
- Day Number: 5
- Type: cultural
- Place: Kyoto
- Transit: Shinkansen from Tokyo

## Timestamp Conversions (Asia/Tokyo = UTC+9)

```
Trip Dates:
- Start: 1735689600 = 2025-01-01 00:00:00 UTC = 2025-01-01 09:00:00 JST
- End:   1736899200 = 2025-01-14 00:00:00 UTC = 2025-01-14 09:00:00 JST

Day 3 (2025-01-03):
- Accommodation Check-in:  1735912800 = 2025-01-03 05:00:00 UTC = 2025-01-03 14:00:00 JST
- Accommodation Check-out: 1735999200 = 2025-01-04 02:00:00 UTC = 2025-01-04 11:00:00 JST
```

## Cost Breakdown (Day 3)

| Item | Cost (¥) | Cost ($) |
|------|----------|----------|
| Meiji Shrine | ¥0 | $0 |
| Shibuya Crossing | ¥0 | $0 |
| teamLab Borderless | ¥3,800 | ~$26 |
| Sukiyabashi Jiro | ¥40,000 | ~$270 |
| **Total** | **¥43,800** | **~$296** |

*Exchange rate: ~¥148 = $1 USD*

## Notes

- All timestamps are Unix timestamps (seconds since epoch)
- Accommodation check-in/check-out times use Unix timestamps
- Activity times use HH:MM format (local time)
- **Duration is in hours (can be decimal):**
  - `0.5` = 30 minutes
  - `1.5` = 1 hour 30 minutes
  - `2.5` = 2 hours 30 minutes
- Costs in activities are in Japanese Yen (¥)
- Trip budget is in USD
