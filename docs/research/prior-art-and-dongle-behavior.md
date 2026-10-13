# Prior art and dongle behavior (research, 2026-10-12)

Read-only desk research. Nothing was posted anywhere. No capture files were opened.

## Method and limits (read first)

- diysolarforum.com returned **HTTP 403 to every direct fetch** (WebFetch and curl). Forum claims below come from
  **search-engine summaries of thread pages**, not from reading the posts, so they are secondary. Post dates and
  usernames were mostly not retrievable; where a date is unknown it says "date unknown". Treat them as leads to
  confirm in a browser.
- Reddit, solarpaneltalk.com and Sol-Ark's support portal were not reached (no usable hits or blocked).
- Primary sources actually read: the Sol-Ark 15K Installation Guide PDF (SK140-0001 Rev 5, 30 Jun 2025), Sol-Ark's
  software-updates page, the Sol-Ark 4G dongle datasheet (19 May 2026), Solar Assistant help pages, and GitHub
  repos/APIs (via `gh`, read-only), plus the Home Assistant community thread.
- Evidence labels: **[Primary]** vendor/repo text read directly; **[Multiple]** two or more independent sources;
  **[Single]** one anecdote; **[Inference]** ours.

## 1. What should change the design (summary)

1. **A documented second data source exists: the inverter's own RS-485 Modbus slave.** The 15K manual states that
   the "Battery CANBus" RJ-45 combines RS-485 and CAN, that "Modbus RS485" and "Battery CANBus" ports "are capable
   of Modbus communication", and that a Modbus map is "available upon request for 'READ' operations only"
   [Primary: 15K Installation Guide p.13]. HA-solark-PV and ESPHome users poll it at 7-20 s [Multiple]. See section 4
   for the honest comparison. It does not replace the tap (the tap sees what the *cloud* does; RS-485 cannot), but the
   firmware design should keep the Modbus decode/register-map layer transport-agnostic so an RS-485 master source
   can be added behind the HAL later.
2. **Firmware-update transport is publicly undocumented.** Nothing found says how the inverter MCU/COMM firmware is
   delivered. Sol-Ark requires the dongle online [Primary/Multiple]. That the bytes ride the DB-9 serial link we tap is
   **our inference**, not confirmed. The recorder must therefore be built for the worst case (see section 2.4).
3. **Upstream author has moved to scraping the dongle's ESP-IDF debug console, not Modbus** (section 6). That is
   fragile and dongle-firmware-specific. Our Modbus-level tap is a genuinely different and more stable approach, and
   upstream is not duplicating it. One upstream issue even tells the author to "consider switching to modbus".
4. **A hardware successor exists**: Sol-Ark 4G dongle SA-DGL-4G (datasheet 19 May 2026) with "Built on PSA Level 3 and
   SESIP Assurance Level 3 Hardware", still a DB9 "Power & RS-232" main connector [Primary]. Our tap is specific to
   `AEM2-0000-05`; the 4G dongle may have a different board/header. Note in the design that the tap is per-dongle-hardware.
5. **The "internal protocol may change" risk is stated by Sol-Ark itself** (support reply quoted in README.md,
   Nov 2025): the serial stream is "not a supported interface" and "can change at any time"; no rollback. The
   firmware should degrade loudly (`link_stale`/unknown-pattern) rather than silently, which the design already does.

## 2. Q1 Inverter and dongle firmware updates

### 2.1 What Sol-Ark says [Primary]
- Remote monitoring and software updates "require an internet connection through the WI-FI / Ethernet Antenna
  (Dongle)" (15K Installation Guide, section on dongle; also: dongle plugs into the inverter's DB-9 port).
- Sol-Ark's update page lists only **COMM** and **MCU** versions per model (15K-2P-LV: COMM 1452, MCU 7228 as of
  fetch) and a scheduling form; it states no delivery method, duration or warnings in the text I could extract
  (https://sol-ark.com/resources/firmware-software-updates/, fetched 2026-10-12). A search-engine summary of the
  older page quotes "15-45 minutes" and "inverter will momentarily turn off for 2-5 minutes"
  (https://www.sol-ark.com/resources/software-updates/) [Single, secondary: not seen in the text I fetched].
- Guide boilerplate: failure to use the most recent firmware "may void your warranty" (15K guide, legal section p.~12).
  So firmware updates are effectively mandatory, and the cloud pushes them.
- 4G dongle datasheet: "Designed for remote communications, firmware updates, and system diagnostics"; platform
  provides "remote firmware updates" (https://sol-ark.com/wp-content/uploads/2026/05/4G_Dongle_Datasheet_Rev1.0_PS-00043_19-May-2026.pdf).

### 2.2 Community reports [secondary, forum summaries]
- "Sol-Ark Firmware Updates" thread: dongle must be plugged in and online; updates are scheduled via Sol-Ark's website
  form or phone; "no file you can download and then upload"; ~2 minutes without power at the end (date unknown)
  https://diysolarforum.com/threads/sol-ark-firmware-updates.120380/ [Single poster].
- Fortress Power's Sol-Ark guide says an update can take up to 60 minutes (2021)
  https://www.fortresspower.com/wp-content/uploads/2021/09/Fortress-Power-Integration-Guide-with-Solark-inverter-Rev2.1.pdf [Single].
- Users report Sol-Ark publishes no changelog and one said support would not say what changed; one said an update
  made the dongle drop offline every couple of days and the next update fixed it
  (https://diysolarforum.com/threads/help-my-sol-ark-dongle-is-offline.36768/ and the firmware thread) [Single each].
- Warning from a poster that units have different hardware needing specific firmware (wrong package could brick)
  [Single, generic].

### 2.3 Bricking
- **No credible report found of a genuine Sol-Ark bricked by an official update.** The only "bricking" hit is
  Deye-built grey-market units sold as Sol-Ark being remotely disabled (Mike Holt forum, secondhand, unverified)
  https://forums.mikeholt.com/threads/sol-ark-counterfeit-inverters-bricking.2584364/ [Single, unverified].
  Absence of evidence in 403-blocked forums is weak; check diysolarforum by hand.

### 2.4 Is the update carried over this serial link? Baud/protocol?
- **Not found anywhere.** No source documents a baud change, bootloader mode, YMODEM, or fc 0x10 file transfer for
  Sol-Ark. Do not claim any.
- **Inference:** the dongle is the inverter's only network path and the serial link is its only data path
  (DB-9 "Power & RS-232", datasheet), so an update most likely traverses it, probably as larger fc16 writes or a
  vendor function code, possibly with a baud change or the inverter dropping out of Modbus into a bootloader (the
  2-5 min power-off window supports a reboot/flash phase). The dongle's own OTA (partitions `factory` + `ota_0`
  in our findings doc) is separate and arrives over Wi-Fi.
- Nov 2025 context: README.md quotes support saying the 15 Oct 2025 release changed "packet restructuring,
  encapsulation changes, and data-handling improvements" and that units "automatically move forward".
  Our findings show the Modbus link itself did not change (the upstream sketch parsed the *console*), so support's
  wording refers to the console/internal format. [Inference, consistent with our captures.]

### 2.5 Dongle self-update (R0.7.0.x, Oct 2025)
- Searches for "R0.7.0", the AEM2 hardware string, `iot.solarkcloud.com` and `pvlimitless` on the web and GitHub code
  search returned **nothing**. The only public account of the Oct 2025 change is the upstream README
  (https://github.com/judasgutenberg/SolArk_Live_Data, commits 2025-11-19, 2026-05-14/15) and the Copilot repo
  (section 6). No forum thread found about it (forums blocked; may exist).
- Dongle firmware version is shown in the dongle web page under Equipment-Gateway (forum, date unknown)
  https://diysolarforum.com/threads/help-my-sol-ark-dongle-is-offline.36768/ [Single].
- A forum user says Sol-Ark support emailed them the dongle firmware as an ESP32 binary
  (https://diysolarforum.com/threads/sol-ark-dongle-not-broadcasting-ssid.98083/ per search summary) [Single, unverified].
  If true, a firmware image could be obtained to understand OTA; do not rely on it.

### 2.6 Recorder requirements implied
Design the anomaly recorder for: (a) silence of **up to ~5 min** (inverter off) and possibly up to the 45-60 min
update window with sparse/odd traffic; (b) the dongle rebooting afterwards (observed: boot read of regs 0-29 then
clock-sync write; truncated frame on power loss) so the "boot sequence" must be a known benign pattern, not an
anomaly; (c) baud change: autobaud fallback already designed; (d) unknown function codes and large fc16 writes;
(e) version registers changing. Sizing: 9600 baud is at most 960 B/s per line, so 45 min = ~2.6 MB per direction
worst case; the ring buffer should be sized in minutes, not frames, and configurable (confirm PSRAM size, already an open
item). [Inference/arithmetic.]

## 3. Q2 Cloud-pushed poll list and settings changes

- Our own evidence (findings doc): console shows the cloud pushing the poll list (`Config version: 8`) and
  `recv server cmd`; poll set can change server-side. **No public source** (forum/GitHub) documents the poll list,
  intervals, or a change history. [Our evidence only.]
- MySolArk official guide: users "remotely adjust inverter settings"; "MUST press Save"; "allow some time for
  MySolArk to upload the settings and the inverter to execute the changes, this will take a few minutes";
  editing needs management permission (https://www.sol-ark.com/wp-content/uploads/2024/05/My_SolArk_User_Guide.pdf,
  and the 15K guide section 6) [Primary/secondary summary].
- "A few minutes" is consistent with cloud -> dongle command -> serial write, but how the write is encoded
  (fc06/fc16 vs vendor) is **not documented publicly**. We saw only the clock-sync fc16. Recommendation stands: capture
  a MySolArk setting change while sampling the tap (a controlled test, e.g. toggling a harmless setting and
  reverting) to verify. Do this only with explicit user approval since it writes to the inverter via the official app.
- Anecdote: a user reported being unable to update parameters through the app after a gateway software update, with
  the app showing stale settings (https://diysolarforum.com/threads/attention-sol-ark-owners-mysolark-version-2-app-is-out.123859/,
  date unknown) [Single]. Same thread: "Live" label still refreshes roughly every 5 minutes [Single]. This matches
  the value of local 10 s data.
- Solar Assistant states "certain inverter models have a read only RS485 port due to the inverter firmware"; for the
  15 kW its compatibility table shows setting control only via the **RS232/WiFi port** (reading of a table by a search
  summary; https://solar-assistant.io/help/ , table not directly read) [Single, secondary]. If right, setting writes
  on a 15K flow only through the dongle's DB-9 link, which makes the tap the **only** place to audit them.

## 4. Q3 Alternatives: honest comparison

| Option | Update rate | Two masters? | Risk / warranty | Verdict |
|---|---|---|---|---|
| **Our passive tap** (inside dongle, listen-only) | 10 s for live blocks (dongle's schedule) | No: we never transmit | Opens dongle (the guide itself shows removing the dongle's cover to fit Ethernet, but not accessing the PCB header); no warranty text found on this; Sol-Ark says the serial stream is unsupported and may change | Keep. Only option that sees cloud writes, firmware traffic, poll-list changes |
| **Inverter RS-485 / "Battery CANBus" RJ-45** (HA-solark-PV, ESPHome, Solar Assistant RS485) | 7-20 s typical (HA-solark-PV README: "at least as fast as every 7 seconds, default 20"); faster feasible, shared bus | **No conflict with the dongle**: separate port; inverter is the slave on both. Conflict is with the *battery BMS* if it uses RS-485 on the same port | 15K guide: "improper use of the communication protocols (CANBUS or MODBUS) will not be covered by warranty"; map on request, READ only; "Only use the CAN port for battery BMS communications" | Strongest alternative for pure telemetry. Adopt as optional second source later; reject as *replacement* because it cannot observe cloud actions |
| **Solar Assistant** | "Fast" metrics within seconds, kWh slow | Pick one connection ("Choose only one") | RS232 route requires removing the dongle (it uses the same DB-9); RS485 route keeps it; 15K needs 2-in-1 BMS splitter unless old firmware | Rejected: commercial, replaces or competes with the dongle path; cloud/dongle audit not possible |
| **ESPHome** (chuyskywalker/solark-esphome, forum users with two 15Ks on one ESP32) | seconds; polling many inverters needs slower rate | None with dongle (RS-485 port) | As RS-485 above | Same as RS-485; useful register map generator and a Sol-Ark Modbus doc converted (author says requested by email 2025-01-15) |
| **ha-solarman / kellerza sunsynk / Solarman stick** | n/a | n/a | These target Deye/Sunsynk Solarman loggers (TCP 8899, V5 protocol). A HA user reported the Sol-Ark **SA-ETH-PWR dongle is not Modbus-TCP compatible** (port 502 closed), Dec 2025 https://community.home-assistant.io/t/sol-ark-hacs-changed-wifi-dongle-to-a-static-ip-address-how-to-reset-network-info/961869 | Not applicable to Sol-Ark's dongle. Sol-Ark's is a different (Espressif, own cloud) logger |
| **Dongle replacement / own master on DB-9 RS-232** | up to 1 s | **Yes if the dongle is also attached.** Solar Assistant's own RS232 mode removes the dongle | Loses MySolArk, remote updates, support posture; Solar Assistant note says only this port gives control on a 15K | Rejected for v1. Our "proxy mode" in Future is the same idea and carries the same two-master and lost-cloud risks |
| **Deye/Sunsynk "dongle hack" sniffing** | n/a | n/a | No passive UART-sniff project for Solarman sticks found; EG4 dongle users sniff to learn which registers it polls (dongle polls a large block ~every 2 min) https://diysolarforum.com/threads/eg4-wifi-ethernet-dongle-installing-esphome.119275/ [Single] | No prior art for our exact approach |

Facts on the RS-485 port [Primary: 15K guide p.13, SK140-0001 Rev 5]: RJ-45 pins 1 = RS-485 B-, 2 = A+, 6 = GND,
7 = A+, 8 = B-; CAN Hi/Lo on pins 4/5. "If an external device utilizes BMS Lithium Batt 00, you must change the Modbus
SN of the inverter to 01, because the default value is 00." Solar Assistant/XtremeOwnage confirm (Modbus ID must be 1
else CRC errors; BMS mode "00") https://static.xtremeownage.com/blog/2023/solar-assistant-with-solark-12k/ [Multiple].
A separate labelled "MODBUS RS-485" jack exists but reports conflict: it "worked for one user at first, then returned
zeros" and "didn't provide the needed data"; most use the Battery CANBus jack via a Y/splitter
(markloveless.net 2024-08-13, https://www.markloveless.net/blog/2024/8/13/energy-monitoring-part-two; diysolarforum
threads, dates unknown) [Multiple, mixed]. Battery CAN-mode and RS-485-Modbus-battery setups can collide
(forum summaries) [Single].

**Honest comparison.** For *telemetry alone*, the RS-485 route is simpler, officially acknowledged (map on request,
READ), does not need to open the dongle, and has several working open-source integrations. Our tap's 10 s cadence
is no better than polling RS-485 every 10 s. The tap's unique value is (1) zero added load on the inverter's Modbus
slave, (2) visibility of the dongle's own traffic: clock sync, any setting writes, poll-list effects, and
firmware-update traffic, which no RS-485 client can see, and (3) no interaction with BMS/parallel settings. Its
costs: opening the dongle, dependence on dongle hardware revision, no faster than the dongle schedule, and no
Sol-Ark acknowledgement. Recommendation: **keep the tap as primary for the recorder/audit goal; record RS-485 as a
considered, conditionally adopted complement**, not as a rejected idea. Warranty exposure: the RS-485 route is
explicitly named in the warranty exclusion for "improper use"; the tap touches only the dongle.

## 5. Q4 Warranty / support stance

- 15K guide [Primary]: damage from "improper use of the communication protocols (CANBUS or MODBUS)" not covered;
  Modbus map "upon request ... READ operations only"; third-party hardware/software "may have a material effect ...
  and could void applicable warranties"; consequential damages disclaimed.
- 30K commercial manual: "Sol-Ark does not support 3rd party usage currently"; map requires NDA (search summary of
  https://www.sol-ark.com/wp-content/uploads/2024/05/30K-3P-208V_Manual-1.pdf) [Single, secondary].
- Sol-Ark support to upstream author (Nov 2025, quoted in README.md): serial stream "not a supported interface";
  engineering "does not provide or support access to that stream for third-party automation"; no rollback [Primary
  (README copy), originally email].
- "Sol-Ark Not covering RS485 communication port under warranty" thread: user says support refused a repair
  involving the RS-485 port https://diysolarforum.com/threads/sol-ark-not-covering-rs485-communication-port-under-warranty.61907/
  [Single anecdote, not read].
- Nothing found specific to opening the dongle. The installer guide itself instructs removing the dongle
  enclosure's cover (for Ethernet), so cover removal is sanctioned; touching its PCB is not addressed.
  [Inference: low-risk to the *inverter* warranty because the tap is passive, but unsupported.]

## 6. Q5 Dongle security

- Default AP password is **public** in the manual: network `EAP-#####` (last 5 digits of dongle serial), a fixed vendor default password (value
  deliberately not recorded here) (15K guide, MySolArk setup step 3) [Primary]. Config page at 10.10.10.1 per the 15K guide; the 2019 8K
  manual used 192.168.8.66 with admin/admin (https://www.fortresspower.com/wp-content/uploads/2019/05/install-owner-Manual-4-15-2019-1.pdf) [Single, old].
  This upgrades the findings-doc claim ("appears to use a trivially guessable default") from inferred to **verified
  by vendor documentation**; our captured value should still stay unrecorded.
- Guide says "DO NOT connect to the EAP-##### network ... The device does not provide internet access"
  [Primary]. It does **not** say the AP is disabled after setup; forum report of an AP that vanished and needed a
  gateway reset via MySolArk (https://diysolarforum.com/threads/sol-ark-dongle-not-broadcasting-ssid.98083/) [Single]
  implies some firmware/states hide it. "Always on" remains our boot-log observation only; not verified by an RF scan.
- Thread titled "sol-ark wifi dongle can connect with default password to configure wifi settings"
  https://diysolarforum.com/threads/sol-ark-wifi-dongle-can-connect-with-default-password-to-configure-wifi-settings.114008/
  [Single, not read]; another thread argues the unit is exposed to intruders via a vulnerability/power button
  [Single opinion, unverified].
- No CVE, advisory, teardown or write-up found for the Sol-Ark dongle, the console credential printing, or
  `AEM2-0000-05`. Plaintext Wi-Fi credentials on the console appear to be **unreported prior art-wise**: a candidate
  responsible disclosure to Sol-Ark. Do not post publicly; coordinate wording with the user (CLAUDE.md rule).
- New 4G dongle claims PSA L3/SESIP L3 hardware security (datasheet). Not proof the AEM2 board is similar.

## 7. Q6 Upstream state

Via GitHub API, read-only, 2026-10-12:
- `judasgutenberg/SolArk_Live_Data`: 11 stars, **1 fork (ours)**, **0 open issues, none ever**; last push
  2026-05-15 (README-only commits; last code commit 2025-10-28). README states the sketch "no longer works"
  after the Oct 2025 change and points to SolArk_Copilot.
- `judasgutenberg/SolArk_Copilot` (ESP8266): last push 2026-07-16, 3 stars, 0 forks, 1 open issue. Active.
  - It adopted a **config-driven line parser** (`serial_parser.md`, `serialparser.cfg`) in 2026-05..07. The sample cfg
    keys are ESP-IDF **console log** fragments and heap addresses (`Characteristic #2;0x3ffb...`,
    `I (318800102)`), i.e. it scrapes the dongle's **debug console** (the same T pad finding in our doc), not Modbus.
    Fragile: addresses and tags are firmware-build specific. It also needs the console, which prints credentials
    (our finding); the repo's sample config contains none.
  - Issue #1 (2026-03-01, user poldim, "consider switching to modbus"): says the upgrade "added a layer of encryption"
    (**claim not supported by our captures: the Modbus link is plain RTU**) and recommends reading the inverter's
    Modbus registers via the ESP and pbix's HA integration (https://github.com/judasgutenberg/SolArk_Copilot/issues/1).
  - Third-party: `pbix/HA-solark-PV` (Modbus-TCP-over-RS485 gateway, pushed 2026-10-10, 55 stars),
    `aaronmelton/solark_monitor` (python register reader, 2026-04), `chuyskywalker/solark-esphome` (2026-06),
    `HammondAutomationHub/HomeAssistant_SolArk` (2026-08), `zorkian/solark_cloud` and `dev-slax/solark_cloud` (cloud API),
    `judasgutenberg/SolArkMonitor` (cloud API).
- No fork or repo found that taps the dongle's Modbus lines, and none that decodes the dongle<->inverter RTU link.
  GitHub code search for `iot.solarkcloud.com` / `AEM2-0000` returned nothing.
- **Duplication check for the planned upstream contribution:** nothing duplicates "Modbus RTU on the dongle's
  internal UART". The useful contribution is the finding (plain 9600 8N1 RTU, poll list, clock-sync write, console
  secrets), plus an offer to supply a stable path. Any contribution should avoid sharing the console log format
  details that leak credentials, and wording is for the user to approve.

## 8. Open follow-ups
1. Read the diysolarforum threads in a browser (403 to tools): firmware-updates 120380, Solar Assistant 15K 78807,
   custom monitoring 121906, dongle SSID 98083, RS485 warranty 61907.
2. Ask Sol-Ark for the Modbus map (READ) as a documentation source for register meanings (verified flags).
3. Controlled test with user approval: change one harmless setting via MySolArk while the tap records, to learn the
   write encoding and latency; ideally also catch a scheduled firmware update with the recorder armed.
4. RF scan to verify whether the dongle AP is always on and its SSID/password pattern (stay within own device).
5. Decide whether to add an RS-485 master transport behind the HAL as an optional second source.
