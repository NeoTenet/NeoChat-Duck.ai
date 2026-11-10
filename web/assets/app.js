(() => {
  'use strict';

  const SESSION_KEY = 'neo_ai_terminal_session';
  const CONVERSATION_KEY = 'neo_ai_terminal_conversation';
  const duckFreeIds = new Set(['claude-haiku-5-5','mistral-small-2603','gpt-6-luna','gpt-5.4-mini','tinfoil/gpt-oss-120b','tinfoil/gemma4-31b']);
  const migrateModelId = value => value === 'api:configured' || String(value || '').startsWith('duckai:') ? value : (duckFreeIds.has(value) ? `duckai:${value}` : 'duckai:gpt-6-luna');
  const makeId = () => crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16); });
  const sessionId = localStorage.getItem(SESSION_KEY) || sessionStorage.getItem(SESSION_KEY) || makeId();
  localStorage.setItem(SESSION_KEY, sessionId);
  let conversationId = localStorage.getItem(CONVERSATION_KEY) || makeId();
  localStorage.setItem(CONVERSATION_KEY, conversationId);

  const i18n = {
    en: {
      workspace:'WORKSPACE',dashboard:'Dashboard',chat:'AI Chat',models:'Models',imageLab:'Image lab',voice:'Voice studio',manage:'MANAGE',activity:'Activity',settings:'Settings',privacyTitle:'Private by design',privacyCopy:'Your workspace runs locally. Chat requests go directly to your selected API provider.',localWorkspace:'LOCAL WORKSPACE',checking:'Checking connection',overview:'OVERVIEW',dashboardTitle:'Dashboard',dashboardSub:'Your AI workspace, at a glance.',newChat:'New conversation',requests:'Total requests',thisSession:'This session',conversations:'Conversations',savedInMemory:'Saved locally',imagesCreated:'Images created',generatedLocally:'Generated to local storage',activeModel:'Active model',readyForRequests:'Ready for requests',aiActivity:'AI activity',activitySub:'Your workspace usage over time',currentSession:'Current session',requestEvents:'request events',activityLegend:'Activity',modelPortfolio:'Model portfolio',modelPortfolioSub:'Configured API model',viewAll:'View all ↗',sixModelsAvailable:'1 configured API model',recentActivity:'Recent activity',recentActivitySub:'Latest actions in this workspace',seeAll:'See all ↗',noActivity:'No activity yet. Start a conversation.',quickActions:'Quick actions',quickActionsSub:'Jump back into your workflow',startChat:'Start a conversation',startChatSub:'Ask any of your AI models',createImage:'Create an image',createImageSub:'Open Duck.ai to use its image tools manually',transcribeAudio:'Transcribe audio',transcribeAudioSub:'Open Duck.ai to use its audio tools manually',chatTitle:'AI Chat',chatSub:'A focused space for ideas, code and answers.',clearChat:'New chat',currentConversation:'Current conversation',memoryNoteTitle:'Saved conversations',memoryNoteCopy:'Your conversations are saved in a local database on this device.',connectedToDuck:'Connected to selected API provider',localSession:'LOCAL SESSION',welcomeTitle:'What can we explore today?',welcomeSub:'Ask a question, explore an idea, or share a file to get started.',attachHint:'Attach image or text file',toSend:'to send',intelligence:'INTELLIGENCE',modelsTitle:'AI Models',modelsSub:'Choose the model that fits your task.',sixAvailable:'1 CONFIGURED',localApiModelsTitle:'Connected API model',localApiModelsSub:'This model is used by the built-in chat with the API key you configured.',duckaiModelsTitle:'All Duck.ai chat models',duckaiModelsSub:'Free, Plus and Pro models are listed here. Open Duck.ai and select the model there.',duckaiToolsTitle:'Duck.ai creative and audio tools',duckaiToolsSub:'Image creation, live voice chat and dictation are Duck.ai product features.',duckaiCatalogNote:'Duck.ai does not provide a public API for these entries. The buttons open the official site; choose the model or tool inside Duck.ai. Availability depends on your Duck.ai plan.',modelInfoTitle:'About model availability',modelInfoCopy:'The model ID is sent to the provider configured in Settings. Model availability and billing are controlled by that provider.',creativeStudio:'CREATIVE STUDIO',imageTitle:'Image lab',imageSub:'Open Duck.ai in your browser to create images manually.',describeImage:'Describe your image',imagePromptSub:'Be as descriptive as you like.',promptLabel:'YOUR PROMPT',imageModelLabel:'Model',generateImage:'Open Duck.ai',imageNote:'Image generation opens Duck.ai manually. Text chat uses your configured API provider.',canvas:'Canvas',canvasSub:'Your generated image will appear here.',waiting:'WAITING',canvasEmptyTitle:'Your canvas is clear',canvasEmptySub:'Describe an image and press generate.',outputFormat:'OUTPUT · JPG / PNG',audioTools:'AUDIO TOOLS',voiceTitle:'Voice studio',voiceSub:'Open Duck.ai in your browser to use audio tools manually.',audioTranscription:'Audio transcription',audioTranscriptionSub:'Open Duck.ai in your browser to use its audio tools manually.',dropAudio:'Drop an audio file here',orBrowse:'or click to browse · up to 25 MB',transcribe:'Open Duck.ai',voicePrivacyNote:'This dashboard does not upload audio. Use Duck.ai manually in your browser.',transcript:'Transcript',transcriptSub:'Recognized speech appears here.',copy:'Copy',transcriptEmpty:'Nothing transcribed yet',liveVoiceTitle:'Live two-way voice',liveVoiceCopy:'The original CLI’s WebRTC live-call mode is preserved. Browser-based live calling is not part of this dashboard build; use <code>python duck_cli.py --voice</code> for the existing feature.',workspaceLog:'WORKSPACE LOG',activityTitle:'Activity',activityPageSub:'A timeline of actions in this browser session.',refresh:'Refresh',sessionTimeline:'Session timeline',activityDisclaimer:'Only actions from this local session are shown.',preferences:'PREFERENCES',settingsTitle:'Settings',settingsSub:'Configure this local workspace.',appearance:'Appearance & language',appearanceSub:'Choose how Neo AI looks and reads.',interfaceLanguage:'Interface language',interfaceLanguageSub:'English or Persian',network:'Network',networkSub:'Optional proxy for in-panel Duck.ai chat, image generation and transcription.',proxyAddress:'Proxy address',proxyAddressSub:'HTTP, HTTPS or SOCKS5 proxy used by the Duck.ai client. Leave blank for a direct connection.',saveSettings:'Save settings',aboutWorkspace:'About this workspace',aboutWorkspaceSub:'Local interface for official provider APIs and Duck.ai manual access.',privacyDetailed:'The dashboard runs locally. Chat prompts and attachments are sent directly to the API provider you configure. API usage may be billed by that provider. Duck.ai is opened separately in your browser for manual use.',localUi:'UI served locally',originalEngine:'Official provider API connection',noApiKey:'API key protected by your operating system',notifications:'Notifications',notificationsEmpty:'You are all caught up.',messages:'messages',noModels:'No model data available.',selected:'SELECTED',chooseModel:'Use model',active:'ACTIVE',modelReady:'Configured provider model',loading:'Loading…',you:'You',assistant:'Neo AI',thinking:'Thinking…',chatError:'The response could not be completed.',chatCleared:'Conversation memory cleared.',modelChanged:'Model updated.',imageStarted:'Creating your image…',imageDone:'Image generated successfully.',transcriptionDone:'Audio transcription complete.',settingsSaved:'Settings saved.',settingsError:'Could not save settings.',requestFailed:'Request failed.',fileTooBig:'File is too large.',attachFiles:'Attached files',imageDownload:'Download image',voiceLoading:'Transcribing audio…',generating:'GENERATING',complete:'COMPLETE',error:'ERROR',activityChat:'Conversation',activityImage:'Image generated',activityVoice:'Audio transcription',activityModel:'Model changed',activitySettings:'Settings updated',activityClear:'Chat cleared',activityError:'Request error',selectAFile:'Choose an audio file first.',typeMessage:'Write a message first.',chatPlaceholder:'Message Neo AI…',reasoning:'Thinking level',reasoningAuto:'Auto',reasoningNone:'Off',reasoningMinimal:'Minimal',reasoningLow:'Low',reasoningMedium:'Medium',reasoningHigh:'High',reasoningXhigh:'Extra deep',reasoningMax:'Maximum',reasoningUnavailable:'Model-managed',conversationNew:'New conversation',conversationEmpty:'No saved conversations yet.',chatSaved:'Conversation saved locally',reasoningPanelTitle:'Model thinking preferences',reasoningPanelSub:'Set a default thinking level for each supported model.',reasoningManaged:'Managed by model',reasoningSaved:'Thinking preference saved',defaultModel:'DEFAULT',providerSettingsTitle:'AI provider connection',providerSettingsSub:'Connect an official API directly to Neo AI Terminal.',providerLabel:'Provider',providerHelp:'Choose the service that will answer chat requests.',providerModelLabel:'Model ID',providerModelHelp:'Enter the exact model ID enabled for your API key.',providerBaseUrl:'API Base URL',providerBaseUrlHelp:'Change this for compatible gateways; official endpoints are prefilled.',providerApiKey:'API key',providerKeyHelp:'Protected by Windows for your user account. Leave blank to keep the saved key.',providerKeySaved:'An API key is saved securely. Leave blank to keep it.',saveProvider:'Save API settings',testProvider:'Test connection',duckManualTitle:'Use Duck.ai manually',duckManualSub:'Open the official Duck.ai website in your browser. This does not use the local API key.',openDuckAi:'Open Duck.ai ↗',providerSaved:'API settings saved.',providerTestOK:'API connection successful.',providerNotConfigured:'Add an API key in Settings to start chatting.',manualAudioTitle:'Audio tools are available on Duck.ai',manualAudioSub:'Open the official website and upload your audio there.',
    },
    fa: {
      workspace:'فضای کاری',dashboard:'داشبورد',chat:'گفتگوی هوشمند',models:'مدل‌ها',imageLab:'آزمایشگاه تصویر',voice:'استودیوی صدا',manage:'مدیریت',activity:'فعالیت‌ها',settings:'تنظیمات',privacyTitle:'حریم خصوصی در اولویت',privacyCopy:'محیط روی دستگاه شما اجرا می‌شود؛ درخواست‌های چت مستقیماً به ارائه‌دهنده API انتخابی ارسال می‌شوند.',localWorkspace:'فضای کاری محلی',checking:'در حال بررسی اتصال',overview:'نمای کلی',dashboardTitle:'داشبورد',dashboardSub:'نمایی کلی از فضای کاری هوش مصنوعی شما.',newChat:'گفتگوی جدید',requests:'مجموع درخواست‌ها',thisSession:'در این نشست',conversations:'گفتگوها',savedInMemory:'ذخیره‌شده روی دستگاه',imagesCreated:'تصاویر ساخته‌شده',generatedLocally:'ذخیره در فضای محلی',activeModel:'مدل فعال',readyForRequests:'آماده دریافت درخواست',aiActivity:'فعالیت هوش مصنوعی',activitySub:'میزان استفاده در طول این نشست',currentSession:'نشست فعلی',requestEvents:'رویداد درخواست',activityLegend:'فعالیت',modelPortfolio:'مجموعه مدل‌ها',modelPortfolioSub:'مدل پیکربندی‌شده برای API',viewAll:'مشاهده همه ↗',sixModelsAvailable:'۱ مدل API پیکربندی‌شده',recentActivity:'فعالیت اخیر',recentActivitySub:'آخرین رویدادهای این فضا',seeAll:'مشاهده همه ↗',noActivity:'هنوز فعالیتی ثبت نشده؛ یک گفتگو شروع کنید.',quickActions:'دسترسی سریع',quickActionsSub:'شروع سریع یک کار جدید',startChat:'شروع گفتگو',startChatSub:'از هرکدام از مدل‌ها سؤال بپرسید',createImage:'ساخت تصویر',createImageSub:'ابزار ساخت تصویر را به‌صورت دستی در Duck.ai باز کنید',transcribeAudio:'تبدیل صدا به متن',transcribeAudioSub:'ابزارهای صوتی Duck.ai را به‌صورت دستی باز کنید',chatTitle:'گفتگوی هوشمند',chatSub:'محیطی متمرکز برای ایده‌ها، کدنویسی و پاسخ‌ها.',clearChat:'گفتگوی جدید',currentConversation:'گفتگوی فعلی',memoryNoteTitle:'گفتگوهای ذخیره‌شده',memoryNoteCopy:'گفتگوها در پایگاه داده محلی همین دستگاه ذخیره می‌شوند.',connectedToDuck:'اتصال به ارائه‌دهنده API انتخابی',localSession:'نشست محلی',welcomeTitle:'امروز چه چیزی را بررسی کنیم؟',welcomeSub:'سؤال بپرسید، ایده‌ای را بررسی کنید یا برای شروع فایل بفرستید.',attachHint:'پیوست عکس یا فایل متنی',toSend:'برای ارسال',intelligence:'هوشمندی',modelsTitle:'مدل‌های هوش مصنوعی',modelsSub:'مدل مناسب کار خود را انتخاب کنید.',sixAvailable:'۱ مدل API پیکربندی‌شده',localApiModelsTitle:'مدل متصل به API',localApiModelsSub:'این مدل در چت داخلی و با کلید API تنظیم‌شده استفاده می‌شود.',duckaiModelsTitle:'تمام مدل‌های گفتگوی Duck.ai',duckaiModelsSub:'مدل‌های رایگان، Plus و Pro اینجا فهرست شده‌اند؛ برای انتخاب نهایی وارد Duck.ai شو.',duckaiToolsTitle:'ابزارهای تصویر و صوت Duck.ai',duckaiToolsSub:'ساخت تصویر، گفتگوی زنده صوتی و دیکته، قابلیت‌های خود Duck.ai هستند.',duckaiCatalogNote:'Duck.ai برای این گزینه‌ها API عمومی ارائه نمی‌کند. دکمه‌ها سایت رسمی را باز می‌کنند و باید مدل یا ابزار را داخل Duck.ai انتخاب کنی. دسترسی به پلن اشتراک بستگی دارد.',modelInfoTitle:'درباره دسترس‌پذیری مدل‌ها',modelInfoCopy:'شناسه مدل به ارائه‌دهنده‌ای که در تنظیمات انتخاب کرده‌اید ارسال می‌شود. دسترسی و هزینه مصرف با همان ارائه‌دهنده است.',creativeStudio:'استودیوی خلاقیت',imageTitle:'آزمایشگاه تصویر',imageSub:'برای ساخت تصویر، Duck.ai را در مرورگر باز کنید.',describeImage:'تصویر خود را توصیف کنید',imagePromptSub:'هرقدر لازم است جزئیات بنویسید.',promptLabel:'شرح تصویر',imageModelLabel:'مدل',generateImage:'بازکردن Duck.ai',imageNote:'ساخت تصویر به‌صورت دستی در Duck.ai انجام می‌شود؛ گفتگوی متنی از API رسمی استفاده می‌کند.',canvas:'بوم تصویر',canvasSub:'تصویر ساخته‌شده در این بخش نمایش داده می‌شود.',waiting:'در انتظار',canvasEmptyTitle:'بوم شما خالی است',canvasEmptySub:'شرح تصویر را بنویسید و ساخت تصویر را بزنید.',outputFormat:'خروجی · JPG / PNG',audioTools:'ابزارهای صوتی',voiceTitle:'استودیوی صدا',voiceSub:'برای استفاده از ابزارهای صوتی، Duck.ai را در مرورگر باز کنید.',audioTranscription:'رونویسی صوتی',audioTranscriptionSub:'برای استفاده از ابزارهای صوتی، Duck.ai را در مرورگر باز کنید.',dropAudio:'فایل صوتی را اینجا رها کنید',orBrowse:'یا برای انتخاب کلیک کنید · حداکثر ۲۵ مگابایت',transcribe:'تبدیل به متن',voicePrivacyNote:'این داشبورد فایل صوتی را بارگذاری نمی‌کند؛ از Duck.ai به‌صورت دستی استفاده کنید.',transcript:'متن رونویسی‌شده',transcriptSub:'گفتار شناسایی‌شده اینجا نمایش داده می‌شود.',copy:'کپی',transcriptEmpty:'هنوز متنی رونویسی نشده است',liveVoiceTitle:'تماس صوتی زنده دوطرفه',liveVoiceCopy:'قابلیت تماس زنده WebRTC نسخه CLI اصلی حفظ شده است. تماس زنده در مرورگر در این نسخه از داشبورد پیاده‌سازی نشده؛ برای استفاده از قابلیت فعلی دستور <code>python duck_cli.py --voice</code> را اجرا کنید.',workspaceLog:'گزارش فضای کاری',activityTitle:'فعالیت‌ها',activityPageSub:'زمان‌بندی رویدادهای همین نشست مرورگر.',refresh:'تازه‌سازی',sessionTimeline:'خط زمانی نشست',activityDisclaimer:'فقط فعالیت‌های همین نشست محلی نمایش داده می‌شوند.',preferences:'ترجیحات',settingsTitle:'تنظیمات',settingsSub:'پیکربندی فضای کاری محلی.',appearance:'ظاهر و زبان',appearanceSub:'زبان رابط کاربری را انتخاب کنید.',interfaceLanguage:'زبان رابط',interfaceLanguageSub:'انگلیسی یا فارسی',network:'شبکه',networkSub:'پروکسی اختیاری برای چت، ساخت تصویر و رونویسی صوتی Duck.ai در همین پنل.',proxyAddress:'نشانی پروکسی',proxyAddressSub:'پروکسی HTTP، HTTPS یا SOCKS5 برای کلاینت Duck.ai؛ برای اتصال مستقیم خالی بگذار.',saveSettings:'ذخیره تنظیمات',aboutWorkspace:'درباره این محیط',aboutWorkspaceSub:'رابط محلی برای APIهای رسمی و استفاده دستی از Duck.ai.',privacyDetailed:'داشبورد روی دستگاه شما اجرا می‌شود. پیام‌ها و فایل‌های پیوست چت مستقیماً به ارائه‌دهنده API انتخابی ارسال می‌شوند و ممکن است هزینه داشته باشند. Duck.ai جداگانه در مرورگر برای استفاده دستی باز می‌شود.',localUi:'رابط کاربری به‌صورت محلی اجرا می‌شود',originalEngine:'اتصال مستقیم به API رسمی ارائه‌دهنده',noApiKey:'کلید API با سیستم‌عامل محافظت می‌شود',notifications:'اعلان‌ها',notificationsEmpty:'اعلان جدیدی ندارید.',messages:'پیام',noModels:'اطلاعات مدلی در دسترس نیست.',selected:'انتخاب‌شده',chooseModel:'انتخاب مدل',active:'فعال',modelReady:'مدل ارائه‌دهنده انتخاب‌شده',loading:'در حال بارگذاری…',you:'شما',assistant:'Neo AI',thinking:'در حال فکر کردن…',chatError:'امکان تکمیل پاسخ وجود نداشت.',chatCleared:'حافظه گفتگو پاک شد.',modelChanged:'مدل تغییر کرد.',imageStarted:'در حال ساخت تصویر…',imageDone:'تصویر با موفقیت ساخته شد.',transcriptionDone:'رونویسی صوتی انجام شد.',settingsSaved:'تنظیمات ذخیره شد.',settingsError:'ذخیره تنظیمات انجام نشد.',requestFailed:'ارسال درخواست ناموفق بود.',fileTooBig:'حجم فایل بیش از حد مجاز است.',attachFiles:'فایل‌های پیوست',imageDownload:'دریافت تصویر',voiceLoading:'در حال تبدیل صدا به متن…',generating:'در حال ساخت',complete:'تکمیل شد',error:'خطا',activityChat:'گفتگو',activityImage:'ساخت تصویر',activityVoice:'رونویسی صوتی',activityModel:'تغییر مدل',activitySettings:'به‌روزرسانی تنظیمات',activityClear:'پاک‌کردن گفتگو',activityError:'خطای درخواست',selectAFile:'ابتدا یک فایل صوتی انتخاب کنید.',typeMessage:'ابتدا یک پیام بنویسید.',chatPlaceholder:'پیام خود را برای Neo AI بنویسید…',reasoning:'سطح تفکر',reasoningAuto:'خودکار',reasoningNone:'خاموش',reasoningMinimal:'حداقلی',reasoningLow:'کم',reasoningMedium:'متوسط',reasoningHigh:'زیاد',reasoningXhigh:'بسیار عمیق',reasoningMax:'حداکثری',reasoningUnavailable:'مدیریت توسط مدل',conversationNew:'گفتگوی جدید',conversationEmpty:'هنوز گفتگوی ذخیره‌شده‌ای ندارید.',chatSaved:'گفتگو به‌صورت محلی ذخیره شد',reasoningPanelTitle:'تنظیم سطح تفکر مدل‌ها',reasoningPanelSub:'سطح پیش‌فرض تفکر هر مدل پشتیبانی‌شده را جداگانه انتخاب کنید.',reasoningManaged:'مدیریت توسط خود مدل',reasoningSaved:'سطح تفکر ذخیره شد',providerSettingsTitle:'اتصال ارائه‌دهنده هوش مصنوعی',providerSettingsSub:'اتصال مستقیم API رسمی به Neo AI Terminal.',providerLabel:'ارائه‌دهنده',providerHelp:'سرویسی را انتخاب کنید که به پیام‌های چت پاسخ می‌دهد.',providerModelLabel:'شناسه مدل',providerModelHelp:'شناسه دقیق مدلی را وارد کنید که کلید API شما اجازه استفاده از آن را دارد.',providerBaseUrl:'آدرس پایه API',providerBaseUrlHelp:'برای درگاه‌های سازگار قابل تغییر است؛ نشانی رسمی از قبل وارد شده است.',providerApiKey:'کلید API',providerKeyHelp:'کلید با حساب ویندوز شما محافظت می‌شود. برای حفظ کلید ذخیره‌شده، این کادر را خالی بگذارید.',providerKeySaved:'کلید API به‌صورت امن ذخیره شده است؛ برای حفظ آن کادر را خالی بگذارید.',saveProvider:'ذخیره تنظیمات API',testProvider:'آزمایش اتصال',duckManualTitle:'استفاده دستی از Duck.ai',duckManualSub:'وب‌سایت رسمی Duck.ai را در مرورگر باز کنید. این روش از کلید API محلی استفاده نمی‌کند.',openDuckAi:'باز کردن Duck.ai ↗',providerSaved:'تنظیمات API ذخیره شد.',providerTestOK:'اتصال API با موفقیت برقرار شد.',providerNotConfigured:'برای شروع گفتگو، در تنظیمات یک کلید API وارد کنید.',manualAudioTitle:'ابزارهای صوتی در Duck.ai در دسترس هستند',manualAudioSub:'سایت رسمی را باز کنید و فایل صوتی را آنجا بارگذاری کنید.'
    }
  };

  Object.assign(i18n.en, {
    privacyCopy: 'Your workspace runs locally. Six free Duck.ai models work inside this panel; official APIs are optional.',
    connectedToDuck: 'Duck.ai Free · in-panel engine',
    networkSub: 'Optional proxy for in-panel Duck.ai chat, image generation and transcription.',
    proxyAddressSub: 'HTTP, HTTPS or SOCKS5 proxy used by the Duck.ai client. Leave blank for a direct connection.',
    aboutWorkspaceSub: 'Local dashboard with six Duck.ai Free models and optional official APIs.',
    privacyDetailed: 'The dashboard and conversation database run locally. Duck.ai prompts and attachments are sent through the retained unofficial DuckAi client. Optional official API requests go to the provider you configure.',
    originalEngine: 'Duck.ai Free models · chat and image generation inside this panel',
    modelReady: 'Ready to use',
    providerNotConfigured: 'Choose a Duck.ai Free model to chat without an API key. The official API model is optional.',
    duckManualTitle: 'Duck.ai Free models are built into this panel',
    duckManualSub: 'Select one of the six Free models in Chat or Models and use it here without opening the Duck.ai website.',
    openDuckAi: 'Generate image',
    imageSub: 'Generate an image here with the selected Duck.ai Free model.',
    imageNote: 'The selected Duck.ai Free model is called from this panel. Daily usage limits may apply.',
    voiceSub: 'Upload an audio file and transcribe it inside this dashboard.',
    audioTranscriptionSub: 'Audio is sent through the original DuckAi client; the transcript appears here.',
    transcribe: 'Transcribe audio',
  });
  Object.assign(i18n.fa, {
    privacyCopy: 'فضای کاری روی دستگاه شما اجرا می‌شود؛ شش مدل رایگان Duck.ai داخل همین پنل قابل استفاده‌اند و اتصال API رسمی اختیاری است.',
    connectedToDuck: 'موتور داخلی مدل‌های رایگان Duck.ai',
    networkSub: 'پروکسی اختیاری برای چت، ساخت تصویر و رونویسی صوتی Duck.ai در همین پنل.',
    proxyAddressSub: 'پروکسی HTTP، HTTPS یا SOCKS5 برای کلاینت Duck.ai؛ برای اتصال مستقیم خالی بگذار.',
    aboutWorkspaceSub: 'داشبورد محلی با شش مدل رایگان Duck.ai و امکان اتصال اختیاری به API رسمی.',
    privacyDetailed: 'داشبورد و تاریخچه گفتگوها روی دستگاه شما اجرا و ذخیره می‌شوند. پیام‌ها و فایل‌های Duck.ai از طریق کلاینت غیررسمی داخلی ارسال می‌شوند؛ استفاده از API رسمی اختیاری است.',
    originalEngine: 'مدل‌های رایگان Duck.ai · چت و ساخت تصویر داخل همین پنل',
    modelReady: 'آماده استفاده',
    providerNotConfigured: 'برای چت بدون کلید API یکی از شش مدل رایگان Duck.ai را انتخاب کن؛ اتصال API رسمی اختیاری است.',
    duckManualTitle: 'مدل‌های رایگان Duck.ai داخل همین پنل هستند',
    duckManualSub: 'یکی از شش مدل رایگان را در بخش چت یا مدل‌ها انتخاب کن و بدون خروج از داشبورد از آن استفاده کن.',
    openDuckAi: 'ساخت تصویر',
    imageSub: 'با مدل رایگان انتخاب‌شده Duck.ai همین‌جا تصویر بساز.',
    imageNote: 'درخواست ساخت تصویر با مدل انتخاب‌شده از همین پنل ارسال می‌شود؛ محدودیت روزانه ممکن است اعمال شود.',
    voiceSub: 'فایل صوتی را بارگذاری کن و همین‌جا متن آن را دریافت کن.',
    audioTranscriptionSub: 'فایل صوتی با کلاینت اصلی DuckAi پردازش می‌شود و متن نتیجه همین‌جا نمایش داده می‌شود.',
    transcribe: 'تبدیل صدا به متن',
  });

  Object.assign(i18n.en, {
    privacyCopy:'Your workspace runs locally. Six Duck.ai Free models run inside this panel; official APIs are optional.',
    modelPortfolioSub:'Six free Duck.ai models + optional official API',
    localApiModelsTitle:'Optional official API model',
    localApiModelsSub:'Configure an API provider in Settings. The six Duck.ai Free models work here without an API key.',
    duckaiModelsTitle:'Six Duck.ai Free models',
    duckaiModelsSub:'Select a model here. It becomes active in the chat selector and Image Lab.',
    duckaiToolsTitle:'Image and audio tools inside the panel',
    duckaiToolsSub:'Create images and transcribe audio without leaving Neo AI Terminal.',
    duckaiCatalogNote:'Duck.ai does not publish a supported public API. This dashboard retains the original unofficial DuckAi client; HTTP 418 challenges, regional restrictions and upstream changes may affect availability.',
    modelInfoCopy:'Duck.ai Free models are sent to the original in-panel DuckAi client. The optional API model uses the provider configured in Settings.',
    imageSub:'Generate an image here using one of the six Duck.ai Free models.',
    imageModelLabel:'Image model', generateImage:'Generate image',
    imageNote:'The selected Duck.ai Free model is used inside this panel. Daily usage limits may apply.',
    voiceSub:'Upload and transcribe audio without leaving the dashboard.',
    audioTranscriptionSub:'Audio is processed through the original DuckAi client.',
    transcribe:'Transcribe audio',
    voicePrivacyNote:'Audio is sent to Duck.ai through the in-panel client for transcription.',
    duckManualTitle:'Duck.ai Free models are available inside this app',
    duckManualSub:'Choose a model from the chat selector or Models page. It runs directly inside Neo AI Terminal.',
    openDuckAi:'Generate image',
    providerNotConfigured:'Choose any Duck.ai Free model to chat without an API key, or configure the optional official API model.',
    modelReady:'Ready to use',
    modelCount:'6 FREE + API',
    localApiBadge:'OPTIONAL API',
    voiceSub:'Upload audio and transcribe it in this dashboard.',
    audioTranscriptionSub:'The selected Duck.ai Free client processes the audio inside this app.',
    transcribe:'Transcribe audio',
    duckManualTitle:'Duck.ai Free models are built into this panel',
    duckManualSub:'Select a Free model from Chat or Models and use it directly here.',
    providerNotConfigured:'Select a Duck.ai Free model to chat without an API key. The official API model is optional.'
  });
  Object.assign(i18n.fa, {
    privacyCopy:'محیط روی دستگاه شما اجرا می‌شود؛ شش مدل رایگان Duck.ai مستقیماً از داخل همین پنل قابل استفاده‌اند.',
    modelPortfolioSub:'شش مدل رایگان Duck.ai به‌همراه API رسمی اختیاری',
    localApiModelsTitle:'مدل API رسمی (اختیاری)',
    localApiModelsSub:'در صورت تمایل، API رسمی را در تنظیمات وصل کن. شش مدل رایگان Duck.ai بدون کلید API در همین پنل کار می‌کنند.',
    duckaiModelsTitle:'شش مدل رایگان Duck.ai',
    duckaiModelsSub:'از همین قسمت مدل را انتخاب کن؛ انتخابت در گفتگوی هوشمند و آزمایشگاه تصویر فعال می‌شود.',
    duckaiToolsTitle:'ابزارهای تصویر و صوت داخل پنل',
    duckaiToolsSub:'بدون خروج از Neo AI Terminal تصویر بساز و فایل صوتی را به متن تبدیل کن.',
    duckaiCatalogNote:'Duck.ai API عمومی و پشتیبانی‌شده ارائه نمی‌کند. این داشبورد از کلاینت غیررسمی اصلی DuckAi استفاده می‌کند؛ خطای ۴۱۸، محدودیت منطقه‌ای و تغییرات سرویس ممکن است دسترسی را مختل کنند.',
    modelInfoCopy:'مدل‌های رایگان Duck.ai از طریق موتور داخلی DuckAi اجرا می‌شوند. مدل API رسمی اختیاری از ارائه‌دهنده تنظیم‌شده در Settings استفاده می‌کند.',
    imageSub:'با انتخاب یکی از شش مدل رایگان Duck.ai همین‌جا تصویر بساز.',
    imageModelLabel:'مدل ساخت تصویر', generateImage:'ساخت تصویر',
    imageNote:'مدل رایگان انتخاب‌شده از داخل همین پنل تصویر می‌سازد؛ محدودیت روزانه ممکن است اعمال شود.',
    voiceSub:'بدون خروج از داشبورد فایل صوتی را بارگذاری و رونویسی کن.',
    audioTranscriptionSub:'فایل صوتی از طریق کلاینت اصلی DuckAi پردازش می‌شود.',
    transcribe:'تبدیل صدا به متن',
    voicePrivacyNote:'فایل صوتی برای رونویسی از داخل پنل به Duck.ai ارسال می‌شود.',
    duckManualTitle:'مدل‌های رایگان Duck.ai داخل همین برنامه هستند',
    duckManualSub:'مدل را از انتخاب‌گر چت یا صفحه مدل‌ها انتخاب کن؛ اجرا مستقیماً داخل Neo AI Terminal انجام می‌شود.',
    openDuckAi:'ساخت تصویر',
    providerNotConfigured:'بدون کلید API یکی از شش مدل رایگان Duck.ai را انتخاب کن؛ یا مدل API رسمی اختیاری را پیکربندی کن.',
    modelReady:'آماده استفاده',
    modelCount:'۶ مدل رایگان + API',
    localApiBadge:'API اختیاری',
    voiceSub:'فایل صوتی را همین‌جا بارگذاری کن و متن آن را دریافت کن.',
    audioTranscriptionSub:'فایل صوتی با مدل انتخابی Duck.ai در همین برنامه پردازش می‌شود.',
    transcribe:'تبدیل صدا به متن',
    duckManualTitle:'مدل‌های رایگان Duck.ai داخل همین پنل هستند',
    duckManualSub:'از بخش گفتگو یا مدل‌ها یک مدل رایگان انتخاب کن و مستقیماً همین‌جا استفاده کن.',
    providerNotConfigured:'برای گفتگو بدون کلید API یکی از مدل‌های رایگان Duck.ai را انتخاب کن. اتصال API رسمی اختیاری است.'
  });

  Object.assign(i18n.en, {
    themeLabel: 'Theme', themeSub: 'Choose dark or light appearance',
    darkTheme: 'Dark theme', lightTheme: 'Light theme',
    switchTheme: 'Switch theme'
  });
  Object.assign(i18n.fa, {
    themeLabel: 'پوسته برنامه', themeSub: 'حالت تیره یا روشن را انتخاب کن',
    darkTheme: 'پوسته تیره', lightTheme: 'پوسته روشن',
    switchTheme: 'تغییر پوسته'
  });

  const $ = (id) => document.getElementById(id);
  const state = { lang: localStorage.getItem('neo_ai_lang') || 'en', models: [], selectedModel: migrateModelId(localStorage.getItem('neo_ai_selected_model')), defaultModel: migrateModelId(localStorage.getItem('neo_ai_default_model') || localStorage.getItem('neo_ai_selected_model')), modelChangeSeq: 0, modelChangeInFlight: false, files: [], busy: false, activities: [], conversations: [], reasoningByModel: JSON.parse(localStorage.getItem('neo_ai_reasoning') || '{}') };
  localStorage.setItem('neo_ai_selected_model', state.selectedModel);
  localStorage.setItem('neo_ai_default_model', state.defaultModel);
  const iconFor = {chat:'◉',image:'▧',voice:'◖',model:'✳',settings:'⚙',clear:'↺',error:'!',default:'⌁'};
  const activityLabel = {chat:'activityChat',image:'activityImage',voice:'activityVoice',model:'activityModel',settings:'activitySettings',clear:'activityClear',error:'activityError'};
  const toneByIndex = ['cyan','pink','violet','blue','green','orange'];

  const THEME_KEY = 'neo_ai_theme';
  const enhancedSelects = new Map();

  function applyTheme(theme) {
    const value = theme === 'light' ? 'light' : 'dark';
    document.documentElement.dataset.theme = value;
    localStorage.setItem(THEME_KEY, value);
    const toggle = $('themeToggle');
    if (toggle) {
      toggle.textContent = value === 'dark' ? '☀' : '☾';
      toggle.title = t('switchTheme');
      toggle.setAttribute('aria-label', t('switchTheme'));
    }
    const selector = $('themeSelect');
    if (selector && selector.value !== value) selector.value = value;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = value === 'light' ? '#edf2fb' : '#171638';
    syncEnhancedSelect(selector);
  }

  function closeEnhancedSelect(controller, returnFocus = false) {
    if (!controller) return;
    controller.wrapper.classList.remove('is-open');
    controller.trigger.setAttribute('aria-expanded', 'false');
    controller.menu.hidden = true;
    controller.menu.style.display = 'none';
    if (returnFocus) controller.trigger.focus();
  }

  function closeAllEnhancedSelects(except = null) {
    for (const controller of enhancedSelects.values()) {
      if (controller !== except) closeEnhancedSelect(controller);
    }
  }

  function syncEnhancedSelect(select) {
    if (!select) return;
    const controller = enhancedSelects.get(select);
    if (!controller) return;
    const selected = select.selectedOptions && select.selectedOptions[0];
    controller.label.textContent = selected ? selected.textContent : '';
    controller.trigger.disabled = !!select.disabled;
    controller.trigger.title = select.title || (selected ? selected.textContent : '');
    controller.trigger.setAttribute('aria-label', select.getAttribute('aria-label') || selected?.textContent || 'Select');
    [...controller.menu.querySelectorAll('[role="option"]')].forEach(button => {
      const active = button.dataset.value === select.value;
      button.setAttribute('aria-selected', active ? 'true' : 'false');
      button.classList.toggle('is-selected', active);
      button.disabled = button.dataset.disabled === 'true';
    });
  }

  function enhanceSelect(select) {
    if (!select || enhancedSelects.has(select)) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'neo-select-wrap';
    if (select.classList.contains('model-picker')) wrapper.classList.add('neo-select-model');
    if (select.classList.contains('reasoning-select')) wrapper.classList.add('neo-select-reasoning');
    if (select.classList.contains('image-model-select')) wrapper.classList.add('neo-select-image');
    if (select.id === 'themeSelect' || select.id === 'languageSelect' || select.id === 'providerSelect') wrapper.classList.add('neo-select-setting');
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);
    select.classList.add('neo-select-native');
    select.tabIndex = -1;
    select.setAttribute('aria-hidden', 'true');

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'neo-select-trigger';
    trigger.setAttribute('role', 'combobox');
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-label', select.getAttribute('aria-label') || select.id || 'Select');
    const label = document.createElement('span');
    label.className = 'neo-select-label';
    const arrow = document.createElement('span');
    arrow.className = 'neo-select-arrow';
    arrow.setAttribute('aria-hidden', 'true');
    arrow.textContent = '⌄';
    trigger.append(label, arrow);

    const menu = document.createElement('div');
    menu.className = 'neo-select-menu';
    menu.id = `neo-select-menu-${select.id || Math.random().toString(36).slice(2)}`;
    menu.setAttribute('role', 'listbox');
    menu.hidden = true;
    trigger.setAttribute('aria-controls', menu.id);
    wrapper.append(trigger);
    document.body.append(menu);

    const controller = {select, wrapper, trigger, label, menu, observer: null};
    enhancedSelects.set(select, controller);

    function rebuild() {
      const current = select.value;
      menu.replaceChildren();
      [...select.options].forEach((option, index) => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'neo-select-option';
        item.setAttribute('role', 'option');
        item.dataset.value = option.value;
        item.dataset.disabled = option.disabled ? 'true' : 'false';
        item.textContent = option.textContent;
        item.disabled = option.disabled;
        item.setAttribute('aria-selected', option.value === current ? 'true' : 'false');
        item.classList.toggle('is-selected', option.value === current);
        item.addEventListener('click', () => {
          if (item.disabled) return;
          select.value = option.value;
          select.dispatchEvent(new Event('change', {bubbles: true}));
          syncEnhancedSelect(select);
          closeEnhancedSelect(controller, true);
        });
        menu.append(item);
      });
      syncEnhancedSelect(select);
    }

    function positionMenu() {
      const rect = trigger.getBoundingClientRect();
      const maxHeight = Math.min(300, Math.max(150, window.innerHeight - 32));
      const below = window.innerHeight - rect.bottom;
      const top = below >= Math.min(maxHeight, menu.scrollHeight || 180) + 12
        ? rect.bottom + 6 : Math.max(8, rect.top - Math.min(maxHeight, menu.scrollHeight || 180) - 6);
      menu.style.left = `${Math.max(8, Math.min(rect.left, window.innerWidth - rect.width - 8))}px`;
      menu.style.top = `${top}px`;
      menu.style.width = `${rect.width}px`;
      menu.style.maxHeight = `${maxHeight}px`;
    }

    function openMenu(focusSelected = false) {
      if (trigger.disabled) return;
      closeAllEnhancedSelects(controller);
      rebuild();
      positionMenu();
      wrapper.classList.add('is-open');
      trigger.setAttribute('aria-expanded', 'true');
      menu.hidden = false;
      menu.style.display = 'grid';
      if (focusSelected) {
        const selected = menu.querySelector('[aria-selected="true"]:not(:disabled)') || menu.querySelector('[role="option"]:not(:disabled)');
        selected?.focus();
      }
    }

    trigger.addEventListener('click', () => {
      if (wrapper.classList.contains('is-open')) closeEnhancedSelect(controller);
      else openMenu(false);
    });
    trigger.addEventListener('keydown', event => {
      if (['ArrowDown','ArrowUp','Enter',' '].includes(event.key)) {
        event.preventDefault();
        openMenu(true);
      }
    });
    menu.addEventListener('keydown', event => {
      const items = [...menu.querySelectorAll('[role="option"]:not(:disabled)')];
      const current = items.indexOf(document.activeElement);
      let next = current;
      if (event.key === 'ArrowDown') next = Math.min(items.length - 1, current + 1);
      else if (event.key === 'ArrowUp') next = Math.max(0, current - 1);
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = items.length - 1;
      else if (event.key === 'Escape') { event.preventDefault(); closeEnhancedSelect(controller, true); return; }
      else return;
      event.preventDefault(); items[next]?.focus();
    });
    select.addEventListener('change', () => syncEnhancedSelect(select));
    controller.observer = new MutationObserver(rebuild);
    controller.observer.observe(select, {childList: true, subtree: true, attributes: true, characterData: true});
    rebuild();
  }

  function enhanceAllSelects() {
    document.querySelectorAll('select.select-control').forEach(enhanceSelect);
  }

  document.addEventListener('click', event => {
    for (const controller of enhancedSelects.values()) {
      if (!controller.wrapper.contains(event.target) && !controller.menu.contains(event.target)) closeEnhancedSelect(controller);
    }
  });
  window.addEventListener('resize', () => closeAllEnhancedSelects());
  window.addEventListener('scroll', () => closeAllEnhancedSelects(), true);

  function t(key) { return (i18n[state.lang] && i18n[state.lang][key]) || i18n.en[key] || key; }
  function applyLanguage(lang) {
    state.lang = lang === 'fa' ? 'fa' : 'en';
    localStorage.setItem('neo_ai_lang', state.lang);
    document.documentElement.lang = state.lang;
    document.documentElement.dir = state.lang === 'fa' ? 'rtl' : 'ltr';
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const value = t(el.dataset.i18n);
      if (value !== undefined) el.innerHTML = value;
    });
    $('languageToggle').textContent = state.lang === 'fa' ? 'EN' : 'فا';
    if ($('themeToggle')) $('themeToggle').title = t('switchTheme');
    $('languageSelect').value = state.lang;
    syncEnhancedSelect($('languageSelect'));
    $('chatInput').placeholder = t('chatPlaceholder');
    $('todayLabel').textContent = new Intl.DateTimeFormat(state.lang === 'fa' ? 'fa-IR' : 'en-US', { dateStyle:'medium' }).format(new Date());
    renderModels(); renderActivities(); updateConversationCount();
    if ($('duckAiModelsGrid')) loadDuckAiCatalog();
  }

  async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set('X-Session-ID', sessionId);
    headers.set('X-Conversation-ID', conversationId);
    if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
    const response = await fetch(path, { ...options, headers });
    if (!response.ok) {
      let message = `${response.status} ${response.statusText}`;
      try { const body = await response.json(); message = body.detail || body.message || message; } catch (_) {}
      throw new Error(message);
    }
    return response;
  }

  function toast(message, type = 'success') {
    const item = document.createElement('div'); item.className = `toast ${type === 'error' ? 'error' : ''}`; item.textContent = message;
    $('toastStack').appendChild(item); setTimeout(() => item.remove(), 3600);
  }

  function navigate(page) {
    const target = document.getElementById(`page-${page}`); if (!target) return;
    document.querySelectorAll('.page-section').forEach(el => el.classList.toggle('active', el === target));
    document.querySelectorAll('.nav-item[data-page]').forEach(el => el.classList.toggle('active', el.dataset.page === page));
    const active = document.querySelector(`.nav-item[data-page="${page}"] span:nth-child(2)`);
    $('crumbCurrent').textContent = active ? active.textContent.trim() : page;
    $('sidebar').classList.remove('open'); $('sidebarScrim').classList.remove('open');
    if (page === 'activity' || page === 'dashboard') refreshState();
  }

  function modelById(id) { return state.models.find(model => model.id === id) || state.models[0]; }
  function buildModelSymbol(model, index) {
    const icons = ['✳','◉','✧','M','O','G'];
    const tone = model.color || toneByIndex[index % toneByIndex.length];
    return `<span class="model-symbol tone-${tone}">${icons[index % icons.length]}</span>`;
  }
  function renderModels() {
    if (!state.models.length) return;
    const activeModel = state.models.some(model => model.id === state.selectedModel) ? state.selectedModel : state.models[0].id;
    state.selectedModel = activeModel;
    const defaultModel = state.models.some(model => model.id === state.defaultModel) ? state.defaultModel : activeModel;
    state.defaultModel = defaultModel;
    const optionMarkup = state.models.map(model => `<option value="${escapeAttr(model.id)}">${escapeHtml(model.name)}</option>`).join('');
    $('chatModelSelect').innerHTML = optionMarkup;
    $('chatModelSelect').value = activeModel;
    syncEnhancedSelect($('chatModelSelect'));
    const imageSelect = $('imageModelSelect');
    if (imageSelect) {
      const freeModels = state.models.filter(item => item.engine === 'duckai');
      imageSelect.innerHTML = freeModels.map(item => `<option value="${escapeAttr(item.id)}">${escapeHtml(item.name)}</option>`).join('');
      imageSelect.value = activeModel.startsWith('duckai:') ? activeModel : (freeModels[0]?.id || 'duckai:gpt-6-luna');
      syncEnhancedSelect(imageSelect);
    }
    $('chatCurrentModel').textContent = modelById(activeModel)?.name || 'Neo AI';
    if ($('chatProviderText')) $('chatProviderText').textContent = modelById(activeModel)?.engine === 'duckai' ? 'Duck.ai Free · In-panel' : (modelById(activeModel)?.provider || 'API provider');
    const chatDefaultBadge = $('chatDefaultBadge');
    if (chatDefaultBadge) { chatDefaultBadge.textContent = t('defaultModel'); chatDefaultBadge.hidden = activeModel !== defaultModel; }
    $('metricModel').textContent = modelById(activeModel)?.name || '—';
    if ($('configuredModelCount')) $('configuredModelCount').textContent = state.lang === 'fa' ? '۶ مدل رایگان + API اختیاری' : '6 FREE MODELS + OPTIONAL API';
    if ($('dashboardModelCount')) $('dashboardModelCount').textContent = state.lang === 'fa' ? '۶ مدل رایگان Duck.ai' : '6 Duck.ai Free models';
    $('dashboardModelList').innerHTML = state.models.map((model, i) => `<button type="button" class="model-row ${model.id === activeModel ? 'selected' : ''}" data-model="${escapeAttr(model.id)}" aria-pressed="${model.id === activeModel ? 'true' : 'false'}">${buildModelSymbol(model,i)}<span class="model-row-info"><b>${escapeHtml(model.name)}</b><small>${escapeHtml(model.engine === 'duckai' ? (state.lang === 'fa' ? 'Duck.ai · رایگان' : 'Duck.ai · Free') : model.provider)}</small></span><span class="model-row-badges">${model.id === defaultModel ? `<span class="default-label">${escapeHtml(t('defaultModel'))}</span>` : ''}${model.id === activeModel ? '<span class="model-status">●</span>' : ''}</span></button>`).join('');
    $('allModelsGrid').innerHTML = state.models.filter(model => model.engine === 'official_api').map((model,i) => `<article class="model-card ${model.id === activeModel ? 'selected' : ''} ${model.id === defaultModel ? 'default-model-card' : ''}" data-select-model="${escapeAttr(model.id)}"><div class="model-card-top">${buildModelSymbol(model,i)}<span class="model-card-badges">${model.id === defaultModel ? `<span class="default-label">${escapeHtml(t('defaultModel'))}</span>` : ''}${model.id === activeModel ? `<span class="selected-label">${escapeHtml(t('selected'))}</span>` : ''}</span></div><h3>${escapeHtml(model.name)}</h3><p>${escapeHtml(model.engine === 'duckai' ? (state.lang === 'fa' ? 'مدل رایگان Duck.ai؛ قابل استفاده مستقیم در همین پنل' : 'Duck.ai Free model · runs directly in this panel') : model.description)}</p><span class="model-id">${escapeHtml(model.id)}</span><div class="model-card-footer"><span>${escapeHtml(model.provider)} · ${escapeHtml(t('modelReady'))}</span><button type="button" data-select-model-button="${escapeAttr(model.id)}" aria-pressed="${model.id === activeModel ? 'true' : 'false'}">${model.id === defaultModel ? escapeHtml(t('defaultModel')) : (model.id === activeModel ? escapeHtml(t('active')) : escapeHtml(t('chooseModel')))}</button></div></article>`).join('');
    refreshReasoningSelect();
    renderReasoningPanel();
  }

  function refreshReasoningSelect() {
    const select = $('reasoningSelect');
    const model = modelById(state.selectedModel);
    const profile = model?.reasoning || {options: [], default: 'auto'};
    const labels = {none:t('reasoningNone'),minimal:t('reasoningMinimal'),low:t('reasoningLow'),medium:t('reasoningMedium'),high:t('reasoningHigh'),xhigh:t('reasoningXhigh'),max:t('reasoningMax')};
    const options = Array.isArray(profile.options) ? profile.options : [];
    if (!options.length) {
      select.innerHTML = `<option value="auto">${escapeHtml(t('reasoningUnavailable'))}</option>`;
      select.disabled = true;
      select.title = t('reasoningUnavailable');
      syncEnhancedSelect(select);
      return;
    }
    select.disabled = false;
    select.innerHTML = options.map(value => `<option value="${escapeAttr(value)}">${escapeHtml(labels[value] || value)}</option>`).join('');
    const saved = state.reasoningByModel[state.selectedModel] || profile.default || options[0];
    select.value = options.includes(saved) ? saved : (profile.default || options[0]);
    select.title = t('reasoning');
    syncEnhancedSelect(select);
  }

  function persistReasoningPreference(modelId, value) {
    state.reasoningByModel[modelId] = value;
    localStorage.setItem('neo_ai_reasoning', JSON.stringify(state.reasoningByModel));
    if (modelId === state.selectedModel) refreshReasoningSelect();
    renderReasoningPanel();
  }

  function saveReasoningPreference() {
    if ($('reasoningSelect').disabled) return;
    persistReasoningPreference(state.selectedModel, $('reasoningSelect').value);
    toast(t('reasoningSaved'));
  }

  function renderReasoningPanel() {
    const grid = $('reasoningSettingsGrid');
    if (!grid || !state.models.length) return;
    const labels = {none:t('reasoningNone'),minimal:t('reasoningMinimal'),low:t('reasoningLow'),medium:t('reasoningMedium'),high:t('reasoningHigh'),xhigh:t('reasoningXhigh'),max:t('reasoningMax')};
    grid.innerHTML = state.models.map(model => {
      const options = Array.isArray(model.reasoning?.options) ? model.reasoning.options : [];
      if (!options.length) return `<div class="reasoning-model-card managed"><div class="reasoning-model-copy"><b>${escapeHtml(model.name)}</b><small>${escapeHtml(model.provider)}</small></div><span class="managed-pill">${escapeHtml(t('reasoningManaged'))}</span></div>`;
      const saved = state.reasoningByModel[model.id];
      const current = options.includes(saved) ? saved : (model.reasoning.default || options[0]);
      const choices = options.map(value => `<option value="${escapeAttr(value)}" ${value === current ? 'selected' : ''}>${escapeHtml(labels[value] || value)}</option>`).join('');
      return `<label class="reasoning-model-card"><span class="reasoning-model-copy"><b>${escapeHtml(model.name)}</b><small>${escapeHtml(model.engine === 'duckai' ? (state.lang === 'fa' ? 'Duck.ai · رایگان' : 'Duck.ai · Free') : model.provider)}</small></span><select class="select-control model-reasoning-select" data-reasoning-model="${escapeAttr(model.id)}" aria-label="${escapeAttr(t('reasoning') + ' ' + model.name)}">${choices}</select></label>`;
    }).join('');
  }

  async function selectModel(modelId) {
    if (!state.models.some(model => model.id === modelId)) {
      toast(state.lang === 'fa' ? 'مدل انتخاب‌شده معتبر نیست.' : 'That model is not available.', 'error');
      return;
    }
    if (state.busy) {
      toast(state.lang === 'fa' ? 'هنگام پاسخ‌گویی امکان تغییر مدل نیست.' : 'Wait until the current response finishes before switching models.', 'error');
      return;
    }
    const requestSeq = ++state.modelChangeSeq;
    state.modelChangeInFlight = true;
    const previousModel = state.selectedModel;
    const previousDefaultModel = state.defaultModel;
    state.selectedModel = modelId;
    state.defaultModel = modelId;
    localStorage.setItem('neo_ai_selected_model', modelId);
    localStorage.setItem('neo_ai_default_model', modelId);
    renderModels();
    document.querySelectorAll('[data-select-model-button], #chatModelSelect').forEach(el => { el.disabled = true; });
    try {
      const response = await api('/api/model', { method:'POST', body:JSON.stringify({model:modelId}) });
      const data = await response.json();
      if (requestSeq !== state.modelChangeSeq) return;
      const confirmedModel = state.models.some(model => model.id === data.model) ? data.model : modelId;
      state.selectedModel = confirmedModel;
      state.defaultModel = confirmedModel;
      localStorage.setItem('neo_ai_selected_model', confirmedModel);
      localStorage.setItem('neo_ai_default_model', confirmedModel);
      renderModels();
      loadDuckAiCatalog();
      toast(t('modelChanged'));
    } catch (error) {
      if (requestSeq === state.modelChangeSeq) {
        state.selectedModel = previousModel;
        state.defaultModel = previousDefaultModel;
        localStorage.setItem('neo_ai_selected_model', previousModel);
        localStorage.setItem('neo_ai_default_model', previousDefaultModel);
        renderModels();
        toast((state.lang === 'fa' ? 'تغییر مدل ذخیره نشد: ' : 'Could not switch model: ') + (error.message || t('requestFailed')), 'error');
      }
    } finally {
      if (requestSeq === state.modelChangeSeq) {
        state.modelChangeInFlight = false;
        document.querySelectorAll('[data-select-model-button], #chatModelSelect').forEach(el => { el.disabled = false; });
      }
    }
  }

  async function loadModels() {
    try { const response = await fetch('/api/models'); const data = await response.json(); state.models = data.models || []; renderModels(); }
    catch (error) { toast(error.message || t('noModels'),'error'); }
  }

  function duckTierLabel(tier) {
    const labels = state.lang === 'fa'
      ? {free:'رایگان', plus:'اشتراک Plus', pro:'اشتراک Pro'}
      : {free:'Free', plus:'Plus subscription', pro:'Pro subscription'};
    return labels[tier] || tier;
  }

  async function loadDuckAiCatalog() {
    const modelsHost = $('duckAiModelsGrid');
    const toolsHost = $('duckAiToolsGrid');
    if (!modelsHost || !toolsHost) return;
    try {
      const response = await fetch('/api/duckai/catalog');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const models = data.free_models || [];
      modelsHost.innerHTML = `<div class="duckai-model-cards">${models.map((model) => {
        const selected = state.selectedModel === model.id;
        return `<article class="duckai-model-card tier-free ${selected ? 'selected' : ''}"><div class="duckai-model-top"><span class="duckai-model-mark">✳</span><span class="duckai-tier-badge tier-free">${state.lang === 'fa' ? 'رایگان' : 'FREE'}</span></div><h4>${escapeHtml(model.name)}</h4><p>${escapeHtml(model.provider)}</p><button type="button" class="duckai-open-btn" data-duckai-model-id="${escapeAttr(model.id)}">${selected ? (state.lang === 'fa' ? 'مدل فعال' : 'Selected') : (state.lang === 'fa' ? 'انتخاب و استفاده' : 'Select & use')}</button></article>`;
      }).join('')}</div>`;
      const labels = state.lang === 'fa'
        ? {image:['ساخت تصویر با هوش مصنوعی','پرامپت را بنویس و خروجی را در همین پنل دریافت کن.','رفتن به آزمایشگاه تصویر'],audio:['تبدیل صدا به متن','فایل صوتی را همین‌جا بارگذاری و رونویسی کن.','رفتن به استودیوی صدا']}
        : {image:['AI image creation','Enter a prompt and view the result in this panel.','Open Image Lab'],audio:['Audio transcription','Upload and transcribe audio without leaving the app.','Open Voice Studio']};
      toolsHost.innerHTML = (data.tools || []).map(tool => {
        const meta = labels[tool.kind] || [tool.name, tool.availability, tool.name];
        const page = tool.kind === 'image' ? 'images' : 'voice';
        return `<article class="duckai-tool-card"><span class="duckai-tool-icon">${tool.kind === 'image' ? '▧' : '⌁'}</span><div class="duckai-tool-copy"><h4>${escapeHtml(meta[0])}</h4><p>${escapeHtml(meta[1])}</p><small>Duck.ai · Free feature</small></div><button type="button" class="duckai-open-btn" data-duckai-page="${page}">${escapeHtml(meta[2])}</button></article>`;
      }).join('');
    } catch (error) {
      modelsHost.innerHTML = `<div class="empty-state">${state.lang === 'fa' ? 'دریافت فهرست مدل‌ها ناموفق بود.' : 'Could not load Duck.ai model list.'}</div>`;
      toolsHost.innerHTML = '';
    }
  }

  // Remove model control tokens before any assistant text reaches the UI.
  function stripStopTokens(value) {
    return String(value ?? '').replace(/<\|(?:im_end|endoftext)\|>/gi, '');
  }

  function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
  function escapeAttr(value) { return escapeHtml(value); }
  function formatTime(timestamp) { const date = new Date(timestamp * 1000); return new Intl.DateTimeFormat(state.lang === 'fa' ? 'fa-IR' : 'en-US', {hour:'2-digit',minute:'2-digit'}).format(date); }
  function renderActivities() {
    const html = state.activities.map(item => {
      const key = activityLabel[item.kind] || 'activity';
      return `<div class="activity-entry"><span class="activity-symbol">${iconFor[item.kind] || iconFor.default}</span><div class="activity-entry-content"><b>${escapeHtml(t(key))} · ${escapeHtml(item.detail || '')}</b><small>${escapeHtml(new Date(item.timestamp * 1000).toLocaleDateString(state.lang === 'fa' ? 'fa-IR' : 'en-US'))}</small></div><span class="activity-time">${formatTime(item.timestamp)}</span></div>`;
    }).join('');
    const empty = `<div class="empty-state">${escapeHtml(t('noActivity'))}</div>`;
    $('recentActivity').innerHTML = html ? state.activities.slice(0,4).map(item => {
      const key = activityLabel[item.kind] || 'activity';
      return `<div class="activity-entry"><span class="activity-symbol">${iconFor[item.kind] || iconFor.default}</span><div class="activity-entry-content"><b>${escapeHtml(t(key))}</b><small>${escapeHtml(item.detail || '')}</small></div><span class="activity-time">${formatTime(item.timestamp)}</span></div>`;
    }).join('') : `<div class="empty-state small-empty">${escapeHtml(t('noActivity'))}</div>`;
    $('fullActivity').innerHTML = html || empty;
    drawChart(state.activities);
  }

  function drawChart(items) {
    const requestEvents = [...items].reverse().filter(item => ['chat','image','voice'].includes(item.kind));
    const buildSeries = kind => {
      const events = requestEvents.filter(item => item.kind === kind);
      const bins = new Array(10).fill(0);
      events.forEach((item,index) => { const bin = Math.min(9, Math.floor(index / Math.max(1, events.length) * 10)); bins[bin] += 1; });
      const max = Math.max(1, ...bins);
      const coords = bins.map((value,index) => ({x:index * (760/9), y:195 - (value/max) * 145}));
      let path = '';
      coords.forEach((point,index) => { if (index === 0) path = `M${point.x.toFixed(1)} ${point.y.toFixed(1)}`; else { const prev = coords[index-1]; const mid = (prev.x + point.x) / 2; path += ` C${mid.toFixed(1)} ${prev.y.toFixed(1)} ${mid.toFixed(1)} ${point.y.toFixed(1)} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`; } });
      return {path,coords,bins};
    };
    const chat = buildSeries('chat'); const images = buildSeries('image'); const voice = buildSeries('voice');
    $('chatLine').setAttribute('d',chat.path); $('imageLine').setAttribute('d',images.path); $('voiceLine').setAttribute('d',voice.path);
    $('chartArea').setAttribute('d',`${chat.path} L760 210 L0 210 Z`);
    $('chartPoints').innerHTML = chat.coords.filter((_,i) => chat.bins[i] > 0).map(point => `<circle class="chart-point" cx="${point.x}" cy="${point.y}" r="4"/>`).join('');
    $('chartTotal').textContent = requestEvents.length;
  }

  function updateConversationCount() { const count = document.querySelectorAll('#messages .message').length; $('conversationCount').textContent = `${count} ${t('messages')}`; }
  async function refreshState() {
    const modelSeqAtStart = state.modelChangeSeq;
    try {
      const response = await api('/api/state'); const data = await response.json();
      if (data.default_model && state.models.some(model => model.id === migrateModelId(data.default_model))) { state.defaultModel = migrateModelId(data.default_model); localStorage.setItem('neo_ai_default_model', data.default_model); }
      if (modelSeqAtStart === state.modelChangeSeq && data.model && state.models.some(model => model.id === migrateModelId(data.model)) && migrateModelId(data.model) !== state.selectedModel && !state.modelChangeInFlight) { state.selectedModel = migrateModelId(data.model); localStorage.setItem('neo_ai_selected_model', state.selectedModel); } state.activities = data.activity || [];
      $('metricRequests').textContent = data.requests ?? 0; $('metricTurns').textContent = data.turns ?? 0; $('metricImages').textContent = data.images ?? 0;
      $('settingsSession').textContent = sessionId.slice(0,8).toUpperCase();
      $('proxyInput').dataset.enabled = data.proxy_enabled ? '1' : '0';
      renderModels(); renderActivities(); updateConversationCount();
    } catch (_) { /* health indicator owns the connection warning */ }
  }

  async function checkHealth() {
    try { const response = await fetch('/api/health'); const data = await response.json(); $('connectionDot').classList.remove('offline'); $('connectionText').textContent = state.lang === 'fa' ? 'متصل' : 'Connected'; }
    catch (_) { $('connectionDot').classList.add('offline'); $('connectionText').textContent = state.lang === 'fa' ? 'قطع اتصال' : 'Disconnected'; }
  }

  function appendMessage(role, text, extra = '') {
    $('welcomeChat').style.display = 'none';
    const isUser = role === 'user';
    const wrapper = document.createElement('div'); wrapper.className = `message ${isUser ? 'user' : 'assistant'}`;
    const avatar = document.createElement('div'); avatar.className = 'message-avatar'; avatar.textContent = isUser ? 'N' : '✳';
    const body = document.createElement('div'); body.className = 'message-body';
    const meta = document.createElement('div'); meta.className = 'message-meta'; meta.textContent = isUser ? t('you') : `${t('assistant')} · ${modelById(state.selectedModel)?.name || ''}`;
    const bubble = document.createElement('div'); bubble.className = 'message-bubble'; bubble.textContent = isUser ? text : stripStopTokens(text);
    body.append(meta,bubble);
    if (extra) { const attach = document.createElement('div'); attach.className = 'message-attachments'; attach.textContent = extra; body.appendChild(attach); }
    wrapper.append(avatar,body); $('messages').appendChild(wrapper); $('messages').scrollTop = $('messages').scrollHeight;
    updateConversationCount(); return bubble;
  }

  function showTyping() {
    const bubble = appendMessage('assistant','');
    bubble.innerHTML = '<span class="typing-dots"><i></i><i></i><i></i></span>';
    return bubble;
  }

  function renderStoredMessages(messages = []) {
    $('messages').querySelectorAll('.message').forEach(el => el.remove());
    $('welcomeChat').style.display = messages.length ? 'none' : 'block';
    for (const message of messages) {
      const bubble = appendMessage(message.role, message.text || '', (message.attachments || []).length ? `${t('attachFiles')}: ${(message.attachments || []).join(', ')}` : '');
      if (message.image_url && message.role === 'assistant') {
        const image = document.createElement('img'); image.src = message.image_url; image.alt = 'Generated image'; image.className = 'stored-chat-image'; bubble.appendChild(image);
      }
    }
    $('messages').scrollTop = $('messages').scrollHeight;
    updateConversationCount();
  }

  async function restoreConversation() {
    try {
      const response = await api('/api/conversation');
      const data = await response.json();
      renderStoredMessages(data.messages || []);
      state.selectedModel = migrateModelId(data.model || state.selectedModel);
      state.defaultModel = migrateModelId(data.default_model || state.defaultModel);
      localStorage.setItem('neo_ai_default_model', state.defaultModel);
      renderModels();
      await loadConversations();
    } catch (error) { toast(error.message || t('requestFailed'),'error'); }
  }

  async function loadConversations() {
    try {
      const response = await api('/api/conversations');
      const data = await response.json(); state.conversations = data.conversations || [];
      const list = $('conversationsList');
      if (!state.conversations.length) { list.innerHTML = `<div class="conversation-empty">${escapeHtml(t('conversationEmpty'))}</div>`; return; }
      list.innerHTML = state.conversations.map(item => `<button type="button" class="conversation-item ${item.id === conversationId ? 'selected' : ''}" data-conversation-id="${escapeAttr(item.id)}"><span class="conversation-dot"></span><span class="conversation-item-copy"><b>${escapeHtml(item.title || t('conversationNew'))}</b><small>${escapeHtml(formatTime(item.updated_at))} · ${Number(item.turns || 0)} ${escapeHtml(t('messages'))}</small></span></button>`).join('');
    } catch (_) { /* conversation list can retry on next refresh */ }
  }

  async function switchConversation(id) {
    if (!id || state.busy || id === conversationId) return;
    conversationId = id; localStorage.setItem(CONVERSATION_KEY, conversationId);
    await restoreConversation();
  }

  async function startNewConversation() {
    if (state.busy) return;
    try {
      const response = await api('/api/conversations/new', {method:'POST'});
      const data = await response.json();
      conversationId = data.conversation_id; localStorage.setItem(CONVERSATION_KEY, conversationId);
      state.files = []; renderAttachmentPreview(); clearChatUI();
      await restoreConversation();
      $('chatInput').focus();
    } catch (error) { toast(error.message || t('requestFailed'),'error'); }
  }

  async function sendChat(event) {
    event.preventDefault(); if (state.busy) return;
    const prompt = $('chatInput').value.trim(); if (!prompt) { toast(t('typeMessage'),'error'); return; }
    state.busy = true; $('sendBtn').disabled = true; $('attachBtn').disabled = true;
    const attached = state.files.map(file => file.name).join(', ');
    appendMessage('user', prompt, attached ? `${t('attachFiles')}: ${attached}` : '');
    const bubble = showTyping();
    const selectedModel = $('chatModelSelect').value || state.selectedModel;
    const effort = $('reasoningSelect').disabled ? '' : $('reasoningSelect').value;
    const attachedFiles = [...state.files];
    $('chatInput').value = ''; state.files = []; renderAttachmentPreview();
    try {
      // If the user attached an image, treat the message as a vision/chat request.
      // Do not misclassify phrases such as "make sense of this picture" as image generation.
      if (looksLikeImageCommand(prompt) && attachedFiles.length === 0) {
        if (!selectedModel.startsWith('duckai:')) throw new Error(state.lang === 'fa' ? 'برای ساخت تصویر باید یکی از شش مدل رایگان Duck.ai را انتخاب کنی.' : 'Select one of the six Duck.ai Free models to generate an image.');
        await requestDuckImage(prompt, selectedModel, bubble);
        state.selectedModel = selectedModel; renderModels();
        await loadConversations(); await refreshState();
      } else {
        const form = new FormData(); form.append('prompt',prompt); form.append('model',selectedModel); if (effort) form.append('reasoning_effort',effort); attachedFiles.forEach(file => form.append('attachments',file));
        const response = await api('/api/chat',{method:'POST',body:form});
        const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer=''; let answer='';
        while (true) {
          const {value,done}=await reader.read(); if(done) break; buffer += decoder.decode(value,{stream:true});
          const lines=buffer.split('\n'); buffer=lines.pop();
          for (const line of lines) { if(!line.trim()) continue; const packet=JSON.parse(line); if(packet.type==='delta'){answer+=packet.text;bubble.textContent=stripStopTokens(answer);$('messages').scrollTop=$('messages').scrollHeight;} else if(packet.type==='error') throw new Error(packet.message || t('chatError')); }
        }
        if(buffer.trim()){const packet=JSON.parse(buffer);if(packet.type==='error')throw new Error(packet.message);if(packet.type==='delta'){answer+=packet.text;bubble.textContent=stripStopTokens(answer);}}
        answer = stripStopTokens(answer); bubble.textContent = answer || '—';
        state.selectedModel=selectedModel; renderModels(); await loadConversations(); await refreshState();
      }
    } catch(error) {
      bubble.textContent = `${t('chatError')}\n${error.message}`;
      bubble.style.borderColor='rgba(255,106,132,.35)';
      // Keep files available after a failed upload/request so the user does not have to reselect them.
      if (attachedFiles.length) { state.files = [...attachedFiles, ...state.files]; renderAttachmentPreview(); }
      if (!$('chatInput').value.trim()) $('chatInput').value = prompt;
      toast(error.message || t('requestFailed'),'error');
    }
    finally { state.busy=false; $('sendBtn').disabled=false; $('attachBtn').disabled=false; $('chatInput').focus(); updateConversationCount(); }
  }

  function addChatFiles(fileList) {
    const incoming = Array.from(fileList || []);
    if (!incoming.length) return;
    const accepted = [];
    for (const file of incoming) {
      const isImage = file.type.startsWith('image/');
      const isText = /\.(txt|md|py|js|json|html|css|csv|xml|ya?ml|log|sql|sh|ts|tsx|jsx|java|go|rs)$/i.test(file.name) || file.type.startsWith('text/');
      if (!isImage && !isText) { toast(state.lang === 'fa' ? `نوع فایل «${file.name}» پشتیبانی نمی‌شود.` : `Unsupported file type: ${file.name}`, 'error'); continue; }
      if (file.size > 12 * 1024 * 1024) { toast(state.lang === 'fa' ? `حجم «${file.name}» بیشتر از ۱۲ مگابایت است.` : `${file.name} is larger than 12 MB.`, 'error'); continue; }
      if (state.files.some(existing => existing.name === file.name && existing.size === file.size && existing.lastModified === file.lastModified)) continue;
      accepted.push(file);
    }
    const room = Math.max(0, 8 - state.files.length);
    state.files.push(...accepted.slice(0, room));
    if (accepted.length > room) toast(state.lang === 'fa' ? 'حداکثر ۸ فایل را می‌توانی هم‌زمان پیوست کنی.' : 'You can attach up to 8 files at once.', 'error');
    renderAttachmentPreview();
  }

  function renderAttachmentPreview() {
    const root = $('attachmentPreview');
    root.replaceChildren();
    state.files.forEach((file, index) => {
      const chip = document.createElement('span'); chip.className = 'attachment-chip';
      if (file.type.startsWith('image/')) {
        const thumb = document.createElement('img'); thumb.className = 'attachment-thumb';
        thumb.alt = ''; thumb.src = URL.createObjectURL(file); chip.appendChild(thumb);
      }
      const name = document.createElement('span'); name.className = 'attachment-name'; name.textContent = file.name; chip.appendChild(name);
      const remove = document.createElement('button'); remove.type = 'button'; remove.dataset.removeFile = String(index); remove.setAttribute('aria-label', state.lang === 'fa' ? 'حذف پیوست' : 'Remove attachment'); remove.textContent = '×'; chip.appendChild(remove);
      root.appendChild(chip);
    });
  }

  function clearChatUI() {
    $('messages').querySelectorAll('.message').forEach(el => el.remove()); $('welcomeChat').style.display = 'block'; $('chatInput').value = ''; updateConversationCount();
  }

  function displayGeneratedImage(container, data) {
    container.innerHTML = '';
    if (data.text) { const caption = document.createElement('p'); caption.className = 'generated-image-caption'; caption.textContent = data.text; container.appendChild(caption); }
    const image = document.createElement('img'); image.src = data.image_url || data.image; image.alt = 'Generated with Duck.ai'; image.className = 'stored-chat-image'; container.appendChild(image);
    const link = document.createElement('a'); link.href = data.image_url || data.image; link.download = data.filename || 'neo-ai-image.png'; link.className = 'image-download'; link.textContent = t('imageDownload'); container.appendChild(link);
  }

  function looksLikeImageCommand(prompt) {
    const fa = /(?:عکس|تصویر).{0,120}(?:بساز|درست\s*کن|ایجاد\s*کن|تولید\s*کن|خلق\s*کن|طراحی\s*کن)|(?:بساز|درست\s*کن|ایجاد\s*کن|تولید\s*کن|خلق\s*کن|طراحی\s*کن).{0,120}(?:عکس|تصویر)/i;
    const en = /\b(?:generate|create|draw|make)\s+(?:(?:me|for me)\s+)?(?:an?\s+)?(?:image|picture|illustration|artwork)\b/i;
    return fa.test(prompt) || en.test(prompt);
  }

  async function requestDuckImage(prompt, model, container) {
    const form = new FormData(); form.append('prompt', prompt); form.append('model', model || 'duckai:gpt-6-luna');
    const response = await api('/api/draw', {method:'POST', body:form});
    const data = await response.json();
    if (!data.ok || !(data.image_url || data.image)) throw new Error(data.detail || t('requestFailed'));
    displayGeneratedImage(container, data);
    return data;
  }

  async function generateImage() {
    const prompt = $('imagePrompt').value.trim();
    if (!prompt) { toast(t('typeMessage'),'error'); $('imagePrompt').focus(); return; }
    const model = $('imageModelSelect')?.value || (state.selectedModel.startsWith('duckai:') ? state.selectedModel : 'duckai:gpt-6-luna');
    const button = $('generateImageBtn'); button.disabled = true;
    $('imageStatus').textContent = t('generating');
    $('imageCanvas').innerHTML = `<div class="canvas-placeholder"><div class="canvas-orbit">✧</div><b>${escapeHtml(t('imageStarted'))}</b></div>`;
    try {
      const data = await requestDuckImage(prompt, model, $('imageCanvas'));
      $('imageStatus').textContent = t('complete');
      $('imageResultFooter').dataset.filename = data.filename || '';
      toast(t('imageDone')); await loadConversations(); await refreshState();
    } catch (error) {
      $('imageStatus').textContent = t('error');
      $('imageCanvas').innerHTML = `<div class="canvas-placeholder"><b>${escapeHtml(t('chatError'))}</b><span>${escapeHtml(error.message)}</span></div>`;
      toast(error.message || t('requestFailed'),'error');
    } finally { button.disabled = false; }
  }

  async function transcribeAudio() {
    const file = $('audioFileInput')?.files?.[0];
    if (!file) { toast(t('selectAFile'),'error'); return; }
    const model = state.selectedModel.startsWith('duckai:') ? state.selectedModel : 'duckai:gpt-6-luna';
    const form = new FormData(); form.append('audio', file); form.append('model', model);
    const button = $('transcribeAudioBtn'); button.disabled = true; button.textContent = t('voiceLoading');
    try { const response = await api('/api/transcribe',{method:'POST',body:form}); const data = await response.json(); $('transcriptOutput').textContent = data.text || '—'; toast(t('transcriptionDone')); await refreshState(); }
    catch (error) { $('transcriptOutput').textContent = error.message; toast(error.message,'error'); }
    finally { button.disabled = false; button.textContent = t('transcribe'); }
  }

  async function loadProviderConfig() {
    try {
      const response = await api('/api/provider/config');
      const config = await response.json();
      const select = $('providerSelect');
      select.innerHTML = (config.providers || []).map(item => `<option value="${escapeAttr(item.id)}" data-base-url="${escapeAttr(item.base_url)}" data-model="${escapeAttr(item.model)}">${escapeHtml(item.label)}</option>`).join('');
      select.value = config.provider;
      syncEnhancedSelect(select);
      $('providerBaseUrl').value = config.base_url || '';
      $('providerModel').value = config.model || '';
      $('providerApiKey').value = '';
      $('providerApiKey').placeholder = config.has_api_key ? '••••••••  (saved securely)' : 'Paste your API key';
      $('providerKeyHint').textContent = config.has_api_key ? t('providerKeySaved') : t('providerKeyHelp');
      state.provider = config.provider;
      state.providerModel = config.model;
    } catch (error) {
      $('providerStatus').textContent = error.message;
    }
  }

  function providerChanged() {
    const option = $('providerSelect').selectedOptions[0];
    if (!option) return;
    // Defaults come from the backend provider catalog, avoiding stale model IDs in the UI.
    $('providerBaseUrl').value = option.dataset.baseUrl || '';
    $('providerModel').value = option.dataset.model || '';
    $('providerApiKey').value = '';
    $('providerApiKey').placeholder = 'Paste your API key';
    $('providerKeyHint').textContent = t('providerKeyHelp');
  }

  async function saveProviderConfig(showToast = true) {
    const payload = {
      provider: $('providerSelect').value,
      base_url: $('providerBaseUrl').value.trim(),
      model: $('providerModel').value.trim(),
      api_key: $('providerApiKey').value.trim() || null
    };
    try {
      const response = await api('/api/provider/config', {method:'POST', body:JSON.stringify(payload)});
      const data = await response.json();
      $('providerApiKey').value = '';
      $('providerApiKey').placeholder = data.has_api_key ? '••••••••  (saved securely)' : 'Paste your API key';
      $('providerKeyHint').textContent = data.has_api_key ? t('providerKeySaved') : t('providerKeyHelp');
      $('providerStatus').textContent = t('providerSaved');
      state.provider = data.provider; state.providerModel = data.model;
      await loadModels(); await refreshState();
      if (showToast) toast(t('providerSaved'));
      return true;
    } catch (error) {
      $('providerStatus').textContent = error.message;
      toast(error.message, 'error');
      return false;
    }
  }

  async function testProviderConfig() {
    const button = $('testProviderConfig'); button.disabled = true;
    try {
      const saved = await saveProviderConfig(false);
      if (!saved) return;
      const response = await api('/api/provider/test', {method:'POST'});
      const result = await response.json();
      $('providerStatus').textContent = `${t('providerTestOK')} ${result.provider} · ${result.model}`;
      toast(t('providerTestOK'));
    } catch (error) {
      $('providerStatus').textContent = error.message;
      toast(error.message, 'error');
    } finally { button.disabled = false; }
  }

  async function saveSettings() {
    const proxy = $('proxyInput').value.trim();
    try { await api('/api/settings',{method:'POST',body:JSON.stringify({proxy:proxy || null})}); $('settingsStatus').textContent = t('settingsSaved'); toast(t('settingsSaved')); }
    catch (error) { $('settingsStatus').textContent = error.message; toast(error.message || t('settingsError'),'error'); }
  }

  // Navigation and interaction wiring
  document.querySelectorAll('.nav-item[data-page]').forEach(btn => btn.addEventListener('click',() => navigate(btn.dataset.page)));
  document.querySelectorAll('[data-go]').forEach(btn => btn.addEventListener('click',() => navigate(btn.dataset.go)));
  $('menuToggle').addEventListener('click',() => {$('sidebar').classList.add('open');$('sidebarScrim').classList.add('open');});
  $('closeSidebar').addEventListener('click',() => {$('sidebar').classList.remove('open');$('sidebarScrim').classList.remove('open');});
  $('sidebarScrim').addEventListener('click',() => {$('sidebar').classList.remove('open');$('sidebarScrim').classList.remove('open');});
  $('languageToggle').addEventListener('click',() => applyLanguage(state.lang === 'en' ? 'fa' : 'en'));
  $('themeToggle')?.addEventListener('click',() => applyTheme(document.documentElement.dataset.theme === 'light' ? 'dark' : 'light'));
  $('themeSelect')?.addEventListener('change',event => applyTheme(event.target.value));
  $('languageSelect').addEventListener('change',event => applyLanguage(event.target.value));
  $('notificationBtn').addEventListener('click',() => $('notificationModal').classList.add('open'));
  $('closeNotifications').addEventListener('click',() => $('notificationModal').classList.remove('open'));
  $('notificationModal').addEventListener('click',event => { if (event.target === $('notificationModal')) $('notificationModal').classList.remove('open'); });
  $('dashboardModelList').addEventListener('click',event => {const row=event.target.closest('[data-model]');if(row) selectModel(row.dataset.model);});
  $('dashboardModelList').addEventListener('keydown',event => {const row=event.target.closest('[data-model]');if(row && (event.key === 'Enter' || event.key === ' ')){event.preventDefault();selectModel(row.dataset.model);}});
  $('allModelsGrid').addEventListener('click',event => {const btn=event.target.closest('[data-select-model-button]');const card=event.target.closest('[data-select-model]');const modelId=btn?.dataset.selectModelButton || card?.dataset.selectModel;if(modelId)selectModel(modelId);});
  $('allModelsGrid').addEventListener('keydown',event => {const button=event.target.closest('[data-select-model-button]');if(button && (event.key === 'Enter' || event.key === ' ')){event.preventDefault();selectModel(button.dataset.selectModelButton);}});
  $('duckAiModelsGrid')?.addEventListener('click', event => { const button = event.target.closest('[data-duckai-model-id]'); if (button) selectModel(button.dataset.duckaiModelId); });
  $('duckAiToolsGrid')?.addEventListener('click', event => { const button = event.target.closest('[data-duckai-page]'); if (button) navigate(button.dataset.duckaiPage); });
  $('chatModelSelect').addEventListener('change',event => selectModel(event.target.value));
  $('reasoningSelect').addEventListener('change', saveReasoningPreference);
  $('reasoningSettingsGrid').addEventListener('change',event => {const select=event.target.closest('[data-reasoning-model]');if(select){persistReasoningPreference(select.dataset.reasoningModel,select.value);toast(t('reasoningSaved'));}});
  $('conversationsList').addEventListener('click',event => {const item=event.target.closest('[data-conversation-id]');if(item)switchConversation(item.dataset.conversationId);});
  $('chatForm').addEventListener('submit',sendChat);
  $('chatInput').addEventListener('keydown',event => {if(event.key === 'Enter' && !event.shiftKey){event.preventDefault();$('chatForm').requestSubmit();}});
  $('chatInput').addEventListener('input',event => {event.target.style.height='auto';event.target.style.height=Math.min(event.target.scrollHeight,130)+'px';});
  $('attachBtn').addEventListener('click',() => $('chatFiles').click());
  $('chatFiles').addEventListener('change',event => {addChatFiles(event.target.files);event.target.value='';});
  $('chatInput').addEventListener('paste',event => { const files = Array.from(event.clipboardData?.items || []).filter(item => item.kind === 'file').map(item => item.getAsFile()).filter(Boolean); if (files.length) { event.preventDefault(); addChatFiles(files); } });
  const composerDropZone = $('chatForm');
  ['dragenter','dragover'].forEach(type => composerDropZone.addEventListener(type,event => { event.preventDefault(); composerDropZone.classList.add('is-dragover'); }));
  ['dragleave','drop'].forEach(type => composerDropZone.addEventListener(type,event => { event.preventDefault(); if (type === 'drop') addChatFiles(event.dataTransfer?.files); composerDropZone.classList.remove('is-dragover'); }));
  window.addEventListener('dragover',event => event.preventDefault()); window.addEventListener('drop',event => { if (!composerDropZone.contains(event.target)) event.preventDefault(); });
  $('attachmentPreview').addEventListener('click',event => {const btn=event.target.closest('[data-remove-file]');if(btn){state.files.splice(Number(btn.dataset.removeFile),1);renderAttachmentPreview();}});
  $('clearChat').addEventListener('click',startNewConversation);
  $('newChatSide').addEventListener('click',startNewConversation);
  document.querySelectorAll('[data-prompt]').forEach(btn => btn.addEventListener('click',() => {$('chatInput').value=btn.dataset.prompt;navigate('chat');$('chatInput').focus();}));
  $('generateImageBtn').addEventListener('click',generateImage);
  $('transcribeAudioBtn')?.addEventListener('click',transcribeAudio);
  $('imageModelSelect')?.addEventListener('change', event => { if (event.target.value && event.target.value !== state.selectedModel) selectModel(event.target.value); });
  $('copyTranscript').addEventListener('click',async() => {try{await navigator.clipboard.writeText($('transcriptOutput').textContent);toast(state.lang==='fa'?'متن کپی شد':'Transcript copied');}catch(_){toast('Clipboard unavailable','error');}});
  $('saveSettings').addEventListener('click',saveSettings);
  $('providerSelect').addEventListener('change',providerChanged);
  $('saveProviderConfig').addEventListener('click',() => saveProviderConfig(true));
  $('testProviderConfig').addEventListener('click',testProviderConfig);
  $('refreshActivity').addEventListener('click',refreshState);

  // Boot
  enhanceAllSelects();
  applyTheme(localStorage.getItem(THEME_KEY) || 'dark');
  applyLanguage(state.lang);
  loadProviderConfig().then(() => loadModels()).then(() => loadDuckAiCatalog()).then(async () => { await restoreConversation(); await refreshState(); });
  checkHealth();
  setInterval(checkHealth,15000);
  setInterval(refreshState,20000);
})();
