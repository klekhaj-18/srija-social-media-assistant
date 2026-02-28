/* Srija Social Media Assistant — Alpine.js Components */

/* ── Theme Manager ─────────────────────────────────────── */
document.addEventListener('alpine:init', () => {
    Alpine.data('themeManager', () => ({
        darkMode: localStorage.getItem('theme') === 'dark' ||
            (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches),
        init() {
            this.$watch('darkMode', v => {
                localStorage.setItem('theme', v ? 'dark' : 'light');
            });
            window.addEventListener('set-theme', e => {
                if (e.detail === 'system') {
                    this.darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
                    localStorage.removeItem('theme');
                } else {
                    this.darkMode = e.detail === 'dark';
                }
            });
        },
    }));

    /* ── App Shell ──────────────────────────────────────── */
    Alpine.data('app', () => ({
        currentPage: 'dashboard',
        toast: { show: false, message: '', type: 'info' },
        _toastTimer: null,

        init() {
            window.addEventListener('navigate-to', e => this.navigate(e.detail.page));
            window.addEventListener('message', e => {
                if (e.data && e.data.type === 'oauth-success') {
                    this.showToast(`Connected to Instagram as @${e.data.name}`, 'success');
                }
            });
        },

        navigate(page) { this.currentPage = page; },

        showToast(message, type = 'info') {
            this.toast = { show: true, message, type };
            clearTimeout(this._toastTimer);
            this._toastTimer = setTimeout(() => this.toast.show = false, 4000);
        },
    }));

    /* ── Dashboard ──────────────────────────────────────── */
    Alpine.data('dashboardPage', () => ({
        connected: false,
        username: '',
        draftCount: 0,
        readyCount: 0,
        publishedCount: 0,
        recentPosts: [],

        async init() {
            try {
                const [igStatus, drafts, history] = await Promise.all([
                    api.get('/auth/instagram/status'),
                    api.get('/drafts/'),
                    api.get('/publish/history'),
                ]);
                this.connected = igStatus.connected;
                this.username = igStatus.username || '';
                this.draftCount = drafts.length;
                this.readyCount = drafts.filter(d => d.status === 'ready').length;
                this.publishedCount = history.length;
                this.recentPosts = history.slice(0, 5);
            } catch (e) {
                console.error('Dashboard load error:', e);
            }
        },
    }));

    /* ── Create Post ───────────────────────────────────── */
    Alpine.data('createPost', () => ({
        contentType: 'lifestyle',
        contentTypes: [
            { value: 'lifestyle', label: 'Lifestyle', desc: 'Everyday moments' },
            { value: 'travel', label: 'Travel', desc: 'Adventures & places' },
            { value: 'food', label: 'Food', desc: 'Delicious content' },
            { value: 'fitness', label: 'Fitness', desc: 'Workouts & health' },
            { value: 'tech', label: 'Tech', desc: 'Gadgets & digital' },
            { value: 'personal_update', label: 'Personal Update', desc: 'Life milestones' },
            { value: 'quote', label: 'Quote', desc: 'Insights & wisdom' },
            { value: 'promotion', label: 'Promotion', desc: 'Subtle promo' },
        ],
        toneSelections: ['casual'],
        tones: [
            { value: 'casual', label: 'Casual' },
            { value: 'aesthetic', label: 'Aesthetic' },
            { value: 'witty', label: 'Witty' },
            { value: 'inspirational', label: 'Inspirational' },
            { value: 'informative', label: 'Informative' },
            { value: 'professional', label: 'Professional' },
            { value: 'friendly', label: 'Friendly' },
            { value: 'exciting', label: 'Exciting' },
        ],
        context: '',
        generating: false,
        chatHistory: [],
        refinementInput: '',
        generatedText: '',

        // Save draft
        draftTitle: '',
        saving: false,

        async generateContent() {
            if (this.generating) return;
            this.generating = true;
            try {
                const res = await api.post('/ai/generate', {
                    content_type: this.contentType,
                    context: this.context,
                    tone: this.toneSelections.join(',') || 'casual',
                    additional_instructions: '',
                    conversation_history: this.chatHistory.length > 0 ? this.chatHistory : [],
                });
                this.generatedText = res.text;
                this.chatHistory.push({ role: 'assistant', content: res.text });
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            } finally {
                this.generating = false;
            }
        },

        async refineContent() {
            if (!this.refinementInput.trim() || this.generating) return;
            this.generating = true;
            const instruction = this.refinementInput;
            this.chatHistory.push({ role: 'user', content: instruction });
            this.refinementInput = '';
            try {
                const res = await api.post('/ai/generate', {
                    content_type: this.contentType,
                    context: this.context,
                    tone: this.toneSelections.join(',') || 'casual',
                    additional_instructions: instruction,
                    conversation_history: this.chatHistory,
                });
                this.generatedText = res.text;
                this.chatHistory.push({ role: 'assistant', content: res.text });
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            } finally {
                this.generating = false;
            }
        },

        async saveDraft() {
            if (!this.draftTitle.trim()) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Please enter a title', type: 'error' } }));
                return;
            }
            this.saving = true;
            try {
                await api.post('/drafts/', {
                    title: this.draftTitle,
                    content_type: this.contentType,
                    body: this.generatedText,
                    status: 'draft',
                });
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Draft saved!', type: 'success' } }));
                // Reset
                this.generatedText = '';
                this.chatHistory = [];
                this.draftTitle = '';
                this.context = '';
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            } finally {
                this.saving = false;
            }
        },

        resetChat() {
            this.chatHistory = [];
            this.generatedText = '';
            this.refinementInput = '';
        },
    }));

    /* ── Drafts Bank ───────────────────────────────────── */
    Alpine.data('draftsBank', () => ({
        drafts: [],
        loading: true,
        viewMode: localStorage.getItem('draftsView') || 'kanban',
        columns: ['idea', 'draft', 'ready', 'scheduled', 'published'],
        columnLabels: { idea: 'Ideas', draft: 'Drafts', ready: 'Ready', scheduled: 'Scheduled', published: 'Published' },

        // Edit modal
        editModal: false,
        editDraft: null,
        editForm: { title: '', content_type: '', body: '', status: '' },

        // Publish modal
        publishModal: false,
        publishDraftId: null,
        publishing: false,

        // Image upload
        uploadingImage: false,

        async init() {
            await this.loadDrafts();
            window.addEventListener('open-draft', e => {
                const draft = this.drafts.find(d => d.id === e.detail.draftId);
                if (draft) this.openEdit(draft);
            });
        },

        async loadDrafts() {
            this.loading = true;
            try {
                this.drafts = await api.get('/drafts/');
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        setView(mode) {
            this.viewMode = mode;
            localStorage.setItem('draftsView', mode);
        },

        draftsByStatus(status) {
            return this.drafts.filter(d => d.status === status);
        },

        openEdit(draft) {
            this.editDraft = draft;
            this.editForm = {
                title: draft.title,
                content_type: draft.content_type,
                body: draft.body,
                status: draft.status,
            };
            this.editModal = true;
        },

        async saveEdit() {
            try {
                const updated = await api.put(`/drafts/${this.editDraft.id}`, this.editForm);
                const idx = this.drafts.findIndex(d => d.id === updated.id);
                if (idx >= 0) this.drafts[idx] = updated;
                this.editModal = false;
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Draft updated', type: 'success' } }));
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            }
        },

        async deleteDraft(id) {
            if (!confirm('Delete this draft?')) return;
            try {
                await api.del(`/drafts/${id}`);
                this.drafts = this.drafts.filter(d => d.id !== id);
                this.editModal = false;
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Draft deleted', type: 'success' } }));
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            }
        },

        openPublish(draftId) {
            this.publishDraftId = draftId;
            this.publishModal = true;
        },

        async publishNow() {
            this.publishing = true;
            try {
                const result = await api.post('/publish/publish', { draft_id: this.publishDraftId });
                if (result.success) {
                    window.dispatchEvent(new CustomEvent('toast', {
                        detail: { message: 'Published to Instagram!', type: 'success' }
                    }));
                    this.publishModal = false;
                    await this.loadDrafts();
                } else {
                    window.dispatchEvent(new CustomEvent('toast', {
                        detail: { message: result.error || 'Publishing failed', type: 'error' }
                    }));
                }
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            } finally {
                this.publishing = false;
            }
        },

        async uploadImage(event) {
            if (!this.editDraft) return;
            const file = event.target.files[0];
            if (!file) return;
            this.uploadingImage = true;
            try {
                const formData = new FormData();
                formData.append('file', file);
                const resp = await fetch(`/api/drafts/${this.editDraft.id}/images`, {
                    method: 'POST',
                    body: formData,
                });
                if (!resp.ok) throw new Error(await resp.text());
                await this.loadDrafts();
                this.editDraft = this.drafts.find(d => d.id === this.editDraft.id);
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Image uploaded', type: 'success' } }));
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Upload failed: ' + e.message, type: 'error' } }));
            } finally {
                this.uploadingImage = false;
                event.target.value = '';
            }
        },

        async deleteImage(draftId, imageId) {
            try {
                await api.del(`/drafts/${draftId}/images/${imageId}`);
                await this.loadDrafts();
                this.editDraft = this.drafts.find(d => d.id === draftId);
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            }
        },

        statusColor(status) {
            const colors = {
                idea: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
                draft: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
                ready: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
                scheduled: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
                published: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
            };
            return colors[status] || '';
        },
    }));

    /* ── Calendar ───────────────────────────────────────── */
    Alpine.data('calendarPage', () => ({
        year: new Date().getFullYear(),
        month: new Date().getMonth(),
        events: [],
        days: [],
        monthNames: ['January','February','March','April','May','June','July','August','September','October','November','December'],
        weekDays: ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],

        async init() {
            await this.loadMonth();
        },

        async loadMonth() {
            const m = `${this.year}-${String(this.month + 1).padStart(2, '0')}`;
            try {
                const res = await api.get(`/calendar/events?month=${m}`);
                this.events = res.events || [];
            } catch (e) {
                console.error(e);
            }
            this.buildDays();
        },

        buildDays() {
            const first = new Date(this.year, this.month, 1);
            const last = new Date(this.year, this.month + 1, 0);
            const startDay = first.getDay();
            this.days = [];
            // Padding
            for (let i = 0; i < startDay; i++) this.days.push(null);
            for (let d = 1; d <= last.getDate(); d++) {
                const dateStr = `${this.year}-${String(this.month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
                this.days.push({
                    day: d,
                    date: dateStr,
                    events: this.events.filter(e => e.date === dateStr),
                    isToday: dateStr === new Date().toISOString().split('T')[0],
                });
            }
        },

        prevMonth() {
            if (this.month === 0) { this.month = 11; this.year--; }
            else this.month--;
            this.loadMonth();
        },
        nextMonth() {
            if (this.month === 11) { this.month = 0; this.year++; }
            else this.month++;
            this.loadMonth();
        },
        today() {
            this.year = new Date().getFullYear();
            this.month = new Date().getMonth();
            this.loadMonth();
        },
    }));

    /* ── Settings ──────────────────────────────────────── */
    Alpine.data('settingsPage', () => ({
        // AI
        anthropicKey: '',
        anthropicConfigured: false,
        testingKey: false,
        testResult: null,

        // Instagram OAuth
        instagramAppId: '',
        instagramAppSecret: '',
        instagramConfigured: false,
        igConnected: false,
        igUsername: '',
        encryptionConfigured: false,

        // Google Drive
        driveCredsFile: '',
        driveFolderId: '',
        driveConfigured: false,

        // Theme
        themeChoice: localStorage.getItem('theme') || 'system',

        async init() {
            try {
                const [aiKeys, oauthCreds, igStatus, driveCreds] = await Promise.all([
                    api.get('/settings/ai-keys'),
                    api.get('/settings/oauth-creds'),
                    api.get('/auth/instagram/status'),
                    api.get('/settings/drive-creds'),
                ]);
                this.anthropicConfigured = aiKeys.anthropic_configured;
                this.instagramConfigured = oauthCreds.instagram_configured;
                this.encryptionConfigured = oauthCreds.encryption_key_configured;
                this.igConnected = igStatus.connected;
                this.igUsername = igStatus.username || '';
                this.driveConfigured = driveCreds.drive_configured;
            } catch (e) {
                console.error(e);
            }
        },

        async saveAIKey() {
            try {
                await api.put('/settings/ai-keys', { anthropic_api_key: this.anthropicKey });
                this.anthropicConfigured = true;
                this.anthropicKey = '';
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'API key saved', type: 'success' } }));
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            }
        },

        async testAIKey() {
            if (!this.anthropicKey) return;
            this.testingKey = true;
            this.testResult = null;
            try {
                const res = await api.post('/settings/test-ai-key', {
                    provider: 'anthropic',
                    api_key: this.anthropicKey,
                });
                this.testResult = res;
            } catch (e) {
                this.testResult = { success: false, message: e.message };
            } finally {
                this.testingKey = false;
            }
        },

        async saveOAuthCreds() {
            try {
                const data = {};
                if (this.instagramAppId) data.instagram_app_id = this.instagramAppId;
                if (this.instagramAppSecret) data.instagram_app_secret = this.instagramAppSecret;
                await api.put('/settings/oauth-creds', data);
                this.instagramConfigured = true;
                this.instagramAppId = '';
                this.instagramAppSecret = '';
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Instagram credentials saved', type: 'success' } }));
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            }
        },

        async generateEncryptionKey() {
            try {
                await api.post('/settings/generate-encryption-key', {});
                this.encryptionConfigured = true;
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Encryption key generated', type: 'success' } }));
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            }
        },

        connectInstagram() {
            api.get('/auth/instagram/login').then(res => {
                window.open(res.url, 'instagram-auth', 'width=600,height=700');
            }).catch(e => {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            });
        },

        async disconnectInstagram() {
            if (!confirm('Disconnect Instagram?')) return;
            try {
                await api.del('/auth/instagram/disconnect');
                this.igConnected = false;
                this.igUsername = '';
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Instagram disconnected', type: 'success' } }));
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            }
        },

        async saveDriveCreds() {
            try {
                const data = {};
                if (this.driveCredsFile) data.google_drive_credentials_file = this.driveCredsFile;
                if (this.driveFolderId) data.google_drive_folder_id = this.driveFolderId;
                await api.put('/settings/drive-creds', data);
                this.driveConfigured = true;
                this.driveCredsFile = '';
                this.driveFolderId = '';
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'Google Drive credentials saved', type: 'success' } }));
            } catch (e) {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: e.message, type: 'error' } }));
            }
        },

        setTheme(choice) {
            this.themeChoice = choice;
            window.dispatchEvent(new CustomEvent('set-theme', { detail: choice }));
        },

        async exportBackup() {
            window.open('/api/settings/export-backup', '_blank');
        },
    }));
});
