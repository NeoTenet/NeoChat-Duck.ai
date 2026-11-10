## v2.5.4 — Duck.ai upstream retry parity and diagnostics
- Restored the original DuckAi bounded retry behavior for HTTP 418 responses returned by the chat endpoint: each retry obtains a fresh handshake, matching the upstream main branch.
- Kept HTTP 451 fail-fast because a country/region rejection is deterministic.
- Added an explicit error phase (`challenge`, `chat_http`, `chat_sse`) so the dashboard can distinguish failure to obtain a challenge token from a rejected chat request or an SSE error.
- Added phase-aware Persian/English-friendly chat and image error descriptions without displaying challenge payloads.
- Confirmed `jsa_jsdom.js` remains byte-identical to the reference repository. The proof metadata and synthetic request-signal structure remain upstream-derived and are not claimed to be a guaranteed fix for Duck.ai-side 418 decisions.

# Neo AI Terminal — UI redesign notes

## What changed

- Switched the Persian UI typography from Vazirmatn to the original Vazir font family. Vazir is loaded from the official Rastikerdar project CDN; English UI continues to use DM Sans.

- Added a local FastAPI wrapper in `web_app.py` around the existing `DuckAI` Python client.
- Added a responsive RecehTok-inspired dark dashboard in `web/` (sidebar, dashboard metrics, glowing multi-series activity chart, model cards, chat workspace, image lab, voice transcription, activity and settings screens).
- Added live streaming chat, image and text-file attachments, image generation, audio-file transcription, model selection, session activity and optional proxy configuration.
- Added Windows and macOS/Linux launch scripts.

## What was intentionally left alone

The existing upstream request implementation and CLI remain in place: `duck_cli.py`, `duck_voice.py`, `duck_i18n.py`, `lang_fa.json`, `jsa_jsdom.js` and the original root `index.html` were not redesigned or rewritten. The dashboard imports and calls the existing `DuckAI` methods.

## Run

```bash
pip install -r requirements.txt
npm install
python web_app.py
```

Open `http://127.0.0.1:8765`.

## Scope and limitations

- The UI is based on the publicly visible RecehTok reference preview; it is an implementation inspired by that layout and visual language, not an imported or pixel-identical Figma file.
- The existing CLI live WebRTC voice call remains available with `python duck_cli.py --voice`. Browser-based live calls are not implemented in this UI build. Audio-file transcription is available in the dashboard.
- Conversation transcripts and engine context are stored locally in `neo_ai_terminal.sqlite3`; the database is created automatically beside `web_app.py` and persists across browser refreshes and server restarts.
- Run on `127.0.0.1` by default. The API has no user authentication; do not expose it to a public network or bind it to `0.0.0.0` without adding an authentication layer and appropriate deployment security.
- Duck.ai is an unofficial upstream dependency. Its endpoints, model availability and rate limits can change independently of this project.


## Conversation persistence and interaction polish

- Added a model-aware reasoning selector to the chat workspace. The selected effort is saved per model in browser local storage and sent with chat requests only for models with configured support.
- Added a SQLite conversation database (`neo_ai_terminal.sqlite3`) with saved conversation titles, transcripts, model context, and a clickable conversation history list. Conversations survive browser refreshes and local server restarts.
- Moved a language switch into the chat toolbar in addition to the global language control.
- Reworked the composer alignment and reduced the send control to a compact 3D-styled arrow button.
- Added smooth message entrances, a continuous welcome emblem/orbit motion, pulsing connection states, and animated typing dots.
- Added the SQLite database to `.gitignore`; the database remains local to each installation.


## Final polish — model controls and layout

- Moved the quick reasoning selector into the chat panel toolbar.
- Added a dedicated per-model reasoning preferences panel on the Models page, with model-managed status for models without a configured profile.
- Applied the Vazir font throughout the Persian UI (not just the language toggle).
- Re-centered composer controls, constrained the send button to a smaller 3D 28px control, and tuned hover/press states.
- Refined continuous emblem/orbit/pulse animations and responsive toolbar wrapping.

- Chat history is stored in SQLite (`neo_ai_terminal.sqlite3`) and survives server restarts; the database is created automatically on first launch.


## 1.2.2 — Model selection and sidebar layout fixes

- Hardened model selection across the chat dropdown, dashboard model list, and model cards. The selected model is confirmed by the API response, synchronized across the UI, and persisted to the active conversation.
- Added accessible button semantics and keyboard support to model selection controls. Prevented duplicate/racing model changes and made request failures visible with a clear message.
- Improved sidebar privacy-card layout so the title, explanatory copy, and local-workspace label remain inside the card and remain readable on shorter screens.
- Added cache-busting asset versions so browsers load the updated JavaScript and CSS after replacing the package.


## 1.3.0 — November 2026
- Persist the selected default model per local browser session in SQLite and use it for new conversations.
- Show a localized default badge in the dashboard model list, model cards, and chat toolbar.
- Apply dark color-scheme styling to native model/reasoning select menus, including dropdown options on Windows.
- Improve chat toolbar identity and language button sizing/alignment to prevent overlap.
- Remove unverified `xhigh` and `max` reasoning values; expose conservative per-model effort options to prevent unsupported high-effort requests.
- Version static assets to bypass stale browser cache.


## 1.4.0 — November 2026
- Set English interface typography to Bebas Neue and Persian interface typography to Vazir.
- Removed the duplicate language control from the chat toolbar; language remains available in the global header and Settings.
- Rebuilt the message composer row as a padded CSS grid and centered the compact 3D send button to prevent edge-hugging in Windows browsers.
- Added continuous smooth motion to dashboard metric sparklines and activity chart traces.
- Updated `run_dashboard.bat` to install missing npm/jsdom and Python dependencies automatically on first launch.
- Added a free PyInstaller Windows build recipe that bundles the Node runtime, jsdom, web assets, and Python backend into a portable folder application.


## 2.0.0 — November 2026
- Added hybrid mode: in-app chat uses official OpenAI, Anthropic, Gemini, or custom OpenAI-compatible APIs.
- Added Settings for provider, model ID, API base URL, secure API key storage, and a connection test.
- Added an **Open Duck.ai** link for manual use in the user's browser; chat no longer uses Duck.ai's private challenge endpoint.
- Added Windows DPAPI protection for saved API keys. API secrets are not returned by the UI.
- Kept the legacy DuckAi CLI, image, and voice modules in the source tree for compatibility; README documents their separate status.


## 2.1.0 — Hybrid API edition

- Added direct streaming adapters for OpenAI Chat Completions, Anthropic Messages, Google Gemini, and OpenAI-compatible gateways.
- Added provider configuration, model ID and connection test settings. API keys are never returned to the browser and use Windows DPAPI on Windows.
- Chat no longer uses Duck.ai's private challenge endpoint.
- Added manual Duck.ai browser links for image and audio tools; legacy private image/transcription routes are disabled in the dashboard.
- Updated provider defaults from a single backend catalog, tightened API Base URL validation, and return an explicit error for empty provider streams.
- Added complete Persian setup guide, Windows EXE build script and GitHub Actions workflow.


## 2.1.1 — Hybrid API hardening
- Fixed the per-browser-session default model preference and synchronize saved preferences when the provider/model is changed.
- Updated dashboard labels to describe official API chat and manual Duck.ai access accurately.
- Removed stale model-count and audio-feature copy that no longer matched the hybrid dashboard.

- Added the required adaptive-thinking mode flag when Claude effort is requested; corrected the Gemini 3.6 Flash profile to include its documented minimal level.


## 2.1.2 — Chat layout and Claude effort reliability
- Rebuilt the chat toolbar as a contained responsive grid; the thinking-level label and selector now stack within the panel and cannot push beyond its width.
- Rebuilt the message composer with a bounded grid, wrapped attachment hint and centered send button; added safe widths for narrow Windows windows and DPI scaling.
- Removed the redundant `thinking: {type: adaptive}` field from Anthropic Messages requests; Claude effort now uses the documented top-level `output_config.effort` parameter.
- Added a migration guard for persisted Duck.ai private URLs and reject Duck.ai/DuckDuckGo web endpoints as API Base URLs.
- Added an explanatory error when an OpenAI-compatible endpoint returns DuckChat challenge payloads.
- Added portable-mode data storage beside the EXE via `portable.flag`, and updated the one-click Windows build ZIP.


## 2.1.3 — Responsive chat controls and Anthropic effort compatibility
- Rebuilt the chat toolbar grid so the model identity and reasoning selector stay inside the panel.
- Centered and constrained the pill composer and send button at desktop, Windows DPI and mobile widths.
- Applied Vazir to Persian UI text and Bebas Neue to English UI text.
- Corrected Anthropic model capability handling: Haiku 4.5 is model-managed; supported Sonnet/Opus models use `output_config.effort`; Opus 4.6–4.8 and Sonnet 4.6 enable adaptive thinking.
- Migrated old Duck.ai catalog model aliases to active Anthropic API model IDs and force-migrated Duck.ai private Base URLs to official provider URLs.


## 2.1.4 — Chat layout stabilization and current Claude 5.5 effort support
- Rebuilt the chat toolbar as a responsive flex/grid layout with bounded labels and a full-width reasoning selector; labels no longer escape the toolbar at common Windows window sizes.
- Rebuilt the chat composer with fixed internal padding, a bounded textarea grid and a centered send button; prevented the pill from overflowing its chat panel.
- Corrected the Anthropic Haiku model mapping: `claude-haiku-5-5` now remains the current API model ID and is no longer downgraded to legacy Haiku 4.5.
- Added model-specific Anthropic effort support. Claude Haiku 5.5 accepts low, medium, high, xhigh and max through `output_config.effort`; legacy Haiku 4.5 remains model-managed.
- Updated the default Anthropic model ID and package version to 2.1.4.
- Automatically migrated the pinned Haiku 4.5 ID written by the previous downgrade bug to current Haiku 5.5.
- Fixed portable ZIP staging so the EXE, marker and data folder are placed at the archive root.


## v2.1.5 — Restore full Duck.ai catalogue
- Restored all currently documented Duck.ai chat models in a dedicated browser-side catalogue (Free/Plus/Pro).
- Added separate Duck.ai tools for image creation, live voice chat and dictation.
- Kept Duck.ai entries separate from direct API models so they cannot accidentally be routed to an unrelated provider API.
- Added explicit notes that public documentation does not disclose image/voice model IDs.
- Added current Plus/Pro model aliases to the preserved legacy CLI model map; Plus/Pro entries remain informational; the six Free entries are now used directly in the dashboard.


## v2.5.3 — Duck.ai models inside the dashboard
- All six Duck.ai Free model entries now route from the model picker into the retained `DuckAI.stream()` client; the optional official API remains separate.
- Image Lab and chat image prompts call the retained `DuckAI.generate_image()` tool and display generated images in the dashboard.
- Voice Studio uses the in-panel audio transcription route instead of sending users to the Duck.ai website.
- Removed external Duck.ai navigation from the UI; model/tool actions stay inside Neo AI Terminal.
- Bundled the original Vazir font package via npm and served it from the local `/fonts` path. Persian typography is larger and more readable; English remains Bebas Neue.
- `run_dashboard.bat` automatically installs missing `jsdom` and Vazir npm dependencies.
- HTTP 418/451 responses now fail fast instead of retrying the private Duck.ai endpoint repeatedly.


## 2.5.3 — In-panel model selection and readable Vazir UI
- The six Duck.ai Free models are selectable from the Models page, dashboard model list and chat toolbar; selection persists as the workspace default.
- Chat requests route to `DuckAI.stream()` with the selected model ID.
- Image prompts in chat and Image Lab route to `DuckAI.generate_image()` with the selected Duck.ai Free model.
- Voice Studio uploads audio to the retained DuckAi transcription client and displays the transcript inside the app.
- Removed all Duck.ai website redirects from active UI controls.
- Updated local Vazir font loading and readable Persian font sizes; English uses Bebas Neue.
- Updated `run_dashboard.bat` to install `jsdom` and Vazir assets automatically when absent.


## 2.5.3
- Added persistent dark/light theme selection.
- Replaced native white Windows select popups with themed, keyboard-accessible dropdowns.
- Improved light-theme contrast for dashboard, chat, models, settings, and composer.


## 2.5.5
- Dark dropdown and navigation options use the dashboard accent color by default and turn white on hover.
- Replaced the boxed Enter hint with a small liquid-glass 3D arrow; removed the “to send / برای ارسال” helper text.
- Added image/file attachment previews, paste-from-clipboard, drag-and-drop, size/type validation and attachment retention after failed requests.
- Fixed image-intent detection so a prompt that includes an attached image is sent as a vision/chat request rather than being misrouted to image generation.
- Hardened multipart upload validation and surfaced image decode errors clearly.

## v2.5.5 — chat attachments and dark-menu polish
- Dark menu option labels now use the dashboard cyan accent and turn white on hover.
- Removed the “↵ to send / برای ارسال” helper text and replaced the boxed keycap with a compact liquid-glass arrow.
- Added image thumbnails, paste-from-clipboard and drag-and-drop attachments.
- Preserve attachments and the prompt after failed chat requests.
- Fixed image-generation intent detection when an image is attached: attached images are sent as chat/vision inputs.
- Added upload count, file-type, empty-file and size checks on both client and server.


## 2.5.6 — Chat usability and reasoning controls

- Kept the New conversation button on one line with a non-wrapping intrinsic width.
- Reworked the chat page as a viewport-bounded flex layout: the message list scrolls independently while the composer remains anchored at the bottom.
- Simplified the composer to three controls only: attachment (+), message input, and send. Removed the extra attach hint and Return/send hint icon.
- Added model-specific Off / Low / Medium / High reasoning controls to Duck.ai model profiles and wired the selection through `/api/chat` into `DuckAI.stream(..., reasoning_effort=...)`. Official API models treat Off as omission of the provider effort parameter.
- Strip `<|im_end|>` and `<|endoftext|>` tokens from streamed, displayed, and persisted assistant output, including when a token is split across stream chunks.


## Version 2.5.6 — chat layout, reasoning and stop-token fixes

- Kept the New conversation button on a single line at desktop and mobile widths.
- Made the message list independently scrollable and kept the composer anchored at the bottom of the chat panel.
- Simplified the composer to exactly three controls: attach (+), message field and send. Removed the extra helper row and Return hint.
- Added Off / Low / Medium / High reasoning choices to supported model profiles and forwarded the selected value to the Duck.ai client or official provider adapter. Duck.ai is an undocumented upstream interface, so individual models may ignore unsupported effort values.
- Removed `<|im_end|>` and `<|endoftext|>` from live, stored and restored assistant output, including tokens split across streamed chunks.


## Version 2.5.7 — final chat controls and layout pass

- The New conversation button now has a non-wrapping width and keeps its Persian label on one line.
- The message stream scrolls inside the chat panel while the full-width composer remains anchored at the bottom and is not clipped.
- The composer contains only the attachment (+), textarea and send button.
- The reasoning menu exposes Off / Low / Medium / High where the selected model profile supports effort; the chosen level is forwarded to the Duck.ai client or official API adapter. Duck.ai's private interface may ignore effort levels for models that do not implement them.
- `<|im_end|>` and `<|endoftext|>` are stripped before display and persistence, including when split across streaming chunks.

## نسخه 2.5.8 — هماهنگی تم تیره و اصلاح payload مدل‌ها
- کارت‌های انتخاب مدل در داشبورد پس‌زمینه سرمه‌ای، متن روشن و حالت انتخاب فیروزه‌ای دارند؛ حالت hover متن را سفید می‌کند.
- اسکرول‌بارها در تم شب باریک و تیره شده‌اند و تم روشن هم اسکرول‌بار هماهنگ خودش را دارد.
- منوهای سفارشی بالاتر از کارت‌ها و سایدبار نمایش داده می‌شوند؛ دکمه «گفتگوی جدید» نیز عرض غیرقابل‌فشرده‌شدن و متن یک‌خطی دارد.
- پروفایل Reasoning به‌ازای هر مدل Duck.ai تعریف شده است. Mistral Small 4 چون حالت Reasoning ندارد، دیگر `reasoningEffort` دریافت نمی‌کند.
- `high` فقط برای GPT-5.4 mini که Extended Reasoning دارد نمایش داده و ارسال می‌شود؛ گزینه‌های قدیمی ناسازگار از ترجیحات ذخیره‌شده نادیده گرفته می‌شوند.
- شناسه مدل‌های رایگان با نگاشت‌های موتور اصلی `duck_cli.MODELS` تست می‌شوند تا شناسه ناشناخته وارد payload نشود.


## نسخه 2.6.0 — رفع نهایی تم تیره و اعتبارسنجی درخواست مدل
- اصلاحات CSS تم شب، کارت‌های مدل، اسکرول‌بار ریشه صفحه و z-index منوها در فایل‌هایی اعمال شد که FastAPI واقعاً از پوشه `web/` سرو می‌کند؛ نسخه‌های تکراری ریشه و `web/assets` همگام شدند.
- کش مرورگر با شناسه نسخه 2.6.0 به‌روزرسانی شد تا CSS/JS جدید پس از جایگزینی بارگیری شود.
- سطح تفکر فقط برای مدل‌هایی ارسال می‌شود که در کاتالوگ Duck.ai قابلیت Reasoning دارند؛ برای Mistral Small 4 پارامتر `reasoningEffort` کاملاً حذف می‌شود.
- سطح `high` فقط برای GPT-5.4 mini که Extended Reasoning دارد پذیرفته می‌شود؛ مقادیر ناسازگار قدیمی قبل از درخواست اصلاح/رد می‌شوند.
- تست‌های رگرسیون برای تم تیره، اسکرول‌بار سند، z-index، همگامی فایل‌های واقعی سرو‌شده و payload مدل‌ها اضافه شدند.


## Version 2.6.0 — served Dark Mode assets and model payload validation
- Applied Dark Mode model-card, document-root scrollbar and dropdown z-index fixes to the actual FastAPI-served `web/` assets; root mirrors and served copies are synchronized.
- Bumped frontend cache keys to 2.6.0 so browsers load the updated CSS and JavaScript.
- Send `reasoningEffort` only for Duck.ai models whose capability profile advertises reasoning; Mistral Small 4 omits the field entirely.
- Accept `high` only for GPT-5.4 mini with Extended Reasoning; stale incompatible saved levels are corrected before requests.
- Added regression checks for Dark Mode styling, root scrollbars, dropdown stacking, served-asset synchronization and model payloads.


## نسخه 2.6.0 — سازگاری شناسه مدل و اصلاح RTL چت

- نام‌های سازگاری `gpt-4o-mini` و `claude-3-haiku` به شناسه‌های canonical مدل‌های رایگان Duck.ai نگاشت می‌شوند؛ شناسه canonical است که به endpoint داخلی ارسال می‌شود.
- شناسه مدل پیش از ساخت payload نرمال‌سازی و اعتبارسنجی می‌شود؛ شناسه ناشناخته پیش از درخواست شبکه رد خواهد شد.
- پارامتر `reasoningEffort` فقط برای مدل‌هایی که در capability map پشتیبانی می‌شوند ارسال می‌شود.
- خطاهای قطعی HTTP 400/401/403/404/422 دیگر چهار بار تکرار نمی‌شوند؛ پیام خطای backend مستقیم‌تر گزارش می‌شود.
- دکمه گفتگوی جدید در زبان فارسی RTL و یک‌خطی شد؛ textarea فارسی از سمت راست و با فاصله مناسب از دکمه پیوست تایپ می‌شود.
- کنتراست نشانگرهای میانبر صفحه‌کلید در تم تاریک و روشن افزایش یافت.


## نسخه 2.6.2 — اعتبارسنجی شناسه مدل و اصلاح RTL
- aliasهای سازگاری `gpt-4o-mini`، `gpt-4o`، `claude-3-haiku` و `claude-3-5-haiku` به شناسه‌های canonical مدل‌های Duck.ai تبدیل می‌شوند؛ نام‌های قدیمی به upstream ارسال نمی‌شوند.
- مدل ناشناخته قبل از هر درخواست شبکه رد می‌شود و بدنه درخواست فقط شامل فیلدهای مورد انتظار کلاینت است؛ پارامتر `reasoningEffort` صرفاً برای مدل‌های پشتیبانی‌کننده اضافه می‌شود.
- خطاهای قطعی HTTP 400/401/403/404/422 بدون handshake و retry اضافی گزارش می‌شوند.
- دکمه گفتگوی جدید با `white-space: nowrap`، `min-width: max-content` و جداسازی bidi متن فارسی در یک خط نمایش داده می‌شود.
- ورودی فارسی دارای `direction: rtl`، `text-align: right` و padding مستقل از دکمه پیوست است.
- بج میانبرهای صفحه‌کلید با متن slate روشن و پس‌زمینه نیمه‌شفاف بهبود یافته است.

## Version 2.6.2 — model ID validation and RTL chat polish
- Compatibility aliases are normalized to canonical current Duck.ai model IDs before an upstream request.
- Unknown IDs are rejected locally; `reasoningEffort` is omitted for models without advertised reasoning support.
- Deterministic HTTP 400/401/403/404/422 failures are not retried with a new handshake.
- Persian New Chat label stays on one line with RTL isolation; the composer textarea is right-aligned and padded away from the attachment control.
- Sidebar keyboard shortcut badges use brighter text and a translucent background.


## Version 2.6.2 — reduced Windows executable footprint

- Switched PyInstaller from onefile to onedir so the main EXE no longer embeds Node.js and npm packages.
- Node.js, jsdom and Vazir assets are shipped beside the EXE in the portable app folder.
- Removed broad collect_all packaging and unused Windows keyring/Uvicorn extras from the lean build requirements.
- Kept a single portable ZIP containing all runtime files and user data folder.
