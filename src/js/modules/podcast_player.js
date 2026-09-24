// =============================================================================
// Risk & Delivery Intelligence Platform — NotebookLM Podcast Audio & Transcript Module
// =============================================================================
import { appState, getLatestWeekKey } from '../state.js';
import { DOM_IDS, getRequiredElement } from '../dom_contract.js';

export function getPodcastScriptForWeek(weekKey) {
    const activeKey = (!weekKey || weekKey === 'present') ? getLatestWeekKey() : weekKey;
    const snap = appState.TIME_MACHINE_SNAPSHOTS[activeKey] || {};
    const podcastScriptMap = appState.CONFIG?.podcastScriptMap || {};

    if (Array.isArray(snap.podcastScript) && snap.podcastScript.length > 0) {
        return snap.podcastScript;
    }
    if (Array.isArray(snap.podcastDialogue) && snap.podcastDialogue.length > 0) {
        return snap.podcastDialogue;
    }
    if (Array.isArray(podcastScriptMap[activeKey]) && podcastScriptMap[activeKey].length > 0) {
        return podcastScriptMap[activeKey];
    }

    return [
        {
            speaker: 'Host A (Lead Architect)',
            time: '00:00',
            text: `Welcome to the Executive Briefing for ${snap.label || activeKey.toUpperCase()}. Today we're reviewing the top risk movements, ATO compliance gates, and active mitigation plans.`
        },
        {
            speaker: 'Host B (Delivery Director)',
            time: '00:24',
            text: `Our key focus this cycle remains closing critical cross-agency dependencies and maintaining zero overdue gap close plans ahead of the steering committee gate.`
        }
    ];
}

export function resolvePodcastAudioSrc(weekKey) {
    const activeKey = (!weekKey || weekKey === 'present') ? getLatestWeekKey() : weekKey;
    const snap = appState.TIME_MACHINE_SNAPSHOTS[activeKey] || {};
    if (snap.hasAudio === false || snap.audioUrl === null) {
        return null;
    }
    if (snap.audioUrl) return snap.audioUrl;
    const configuredMap = appState.CONFIG?.podcastAudioMap || {};
    if (configuredMap[activeKey]) return configuredMap[activeKey];
    return `assets/podcast_${activeKey}.mp3`;
}

export async function hasAudioForWeek(weekKey) {
    const activeKey = (!weekKey || weekKey === 'present') ? getLatestWeekKey() : weekKey;
    if (activeKey in appState.PODCAST_AUDIO_CACHE) {
        return appState.PODCAST_AUDIO_CACHE[activeKey];
    }
    const snap = appState.TIME_MACHINE_SNAPSHOTS[activeKey] || {};
    if (snap.hasAudio === false || snap.audioUrl === null) {
        appState.PODCAST_AUDIO_CACHE[activeKey] = false;
        return false;
    }
    const src = resolvePodcastAudioSrc(activeKey);
    if (!src) {
        appState.PODCAST_AUDIO_CACHE[activeKey] = false;
        return false;
    }
    try {
        const resp = await fetch(src, { method: 'HEAD' });
        const exists = resp.ok;
        appState.PODCAST_AUDIO_CACHE[activeKey] = exists;
        return exists;
    } catch {
        appState.PODCAST_AUDIO_CACHE[activeKey] = false;
        return false;
    }
}

export function getPodcastAudioElement() {
    return document.getElementById('nativePodcastAudio') || document.getElementById('briefingPodcastAudio');
}

export async function updatePodcastAudioForWeek(weekKey) {
    const activeKey = (!weekKey || weekKey === 'present') ? getLatestWeekKey() : weekKey;
    const audioEl = getPodcastAudioElement();
    const src = resolvePodcastAudioSrc(activeKey);
    const hasAudio = await hasAudioForWeek(activeKey);
    const titleEl = document.getElementById(DOM_IDS.PODCAST_TITLE_TEXT);
    const timeLabel = document.getElementById(DOM_IDS.PODCAST_TIME_LABEL);
    const snap = appState.TIME_MACHINE_SNAPSHOTS[activeKey] || {};

    if (titleEl) {
        titleEl.innerText = snap.podcastTitle || (snap.label ? `${snap.label} Briefing` : 'The I-129 Breakthrough & SRR Glide Path');
    }

    if (audioEl) {
        if (!audioEl.__listenersAttached) {
            audioEl.addEventListener('ended', () => {
                appState.isPodcastPlaying = false;
                const playBtn = document.getElementById(DOM_IDS.PODCAST_PLAY_BTN);
                if (playBtn) playBtn.innerText = '▶';
                animateWaveform(false);
            });
            audioEl.addEventListener('pause', () => {
                appState.isPodcastPlaying = false;
                const playBtn = document.getElementById(DOM_IDS.PODCAST_PLAY_BTN);
                if (playBtn) playBtn.innerText = '▶';
                animateWaveform(false);
            });
            audioEl.__listenersAttached = true;
        }

        if (hasAudio && src) {
            if (audioEl.getAttribute('src') !== src) {
                audioEl.setAttribute('src', src);
                const sourceEl = document.getElementById('nativePodcastSourceMp3');
                if (sourceEl) sourceEl.setAttribute('src', src);
                audioEl.load();
            }
        } else {
            stopSpeechSynthesis();
            audioEl.src = '';
            audioEl.removeAttribute('src');
            const sourceEl = document.getElementById('nativePodcastSourceMp3');
            if (sourceEl) {
                sourceEl.src = '';
                sourceEl.removeAttribute('src');
            }
            audioEl.load();
        }
    }

    const playBtn = document.getElementById(DOM_IDS.PODCAST_PLAY_BTN);
    const transcriptBtn = document.getElementById('podcastTranscriptBtn');
    const downloadLink = document.getElementById(DOM_IDS.PODCAST_DOWNLOAD_LINK);

    const script = getPodcastScriptForWeek(activeKey);
    const hasScript = Array.isArray(script) && script.length > 0;

    if (timeLabel) {
        timeLabel.innerText = hasAudio ? '0:00 / 1:45' : '0:00 / Script Dialogue';
    }

    if (playBtn) {
        // Keep Play button enabled if studio audio is available OR script dialogue is available for speech synthesis
        const canPlay = hasAudio || hasScript;
        playBtn.disabled = !canPlay;
        playBtn.classList.toggle('opacity-50', !canPlay);
        if (canPlay && !hasAudio) {
            playBtn.title = 'Play Dialogue (Speech Synthesis Fallback)';
        } else if (canPlay) {
            playBtn.title = 'Play Executive Audio Briefing';
        }
    }
    if (transcriptBtn) {
        transcriptBtn.disabled = false;
    }
    if (downloadLink) {
        if (hasAudio && src) {
            downloadLink.setAttribute('href', src);
            downloadLink.setAttribute('download', `podcast_${activeKey}.mp3`);
            downloadLink.classList.remove('opacity-50', 'pointer-events-none');
        } else {
            downloadLink.removeAttribute('href');
            downloadLink.classList.add('opacity-50', 'pointer-events-none');
        }
    }
    renderPodcastTranscript(activeKey);
}

export function formatAudioTime(seconds) {
    if (!seconds || isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

export function animateWaveform(active) {
    if (appState.podcastAnimationInterval) {
        clearInterval(appState.podcastAnimationInterval);
        appState.podcastAnimationInterval = null;
    }
    const bars = document.querySelectorAll('.waveform-bar');
    if (!active) {
        bars.forEach(b => {
            b.style.height = '25%';
        });
        return;
    }
    appState.podcastAnimationInterval = setInterval(() => {
        bars.forEach(b => {
            const h = Math.floor(Math.random() * 75) + 20;
            b.style.height = `${h}%`;
        });
    }, 180);
}

export function stopSpeechSynthesis() {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
    appState.isPodcastPlaying = false;
    const playBtn = document.getElementById('podcastPlayBtn');
    if (playBtn) playBtn.innerText = '▶';
    animateWaveform(false);
}

export function playSpeechSynthesisDialogue(startIndex = 0) {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
        console.warn('SpeechSynthesis is not supported in this environment.');
        return;
    }
    const script = getPodcastScriptForWeek(appState.activeTimeMachineWeek);
    if (!Array.isArray(script) || script.length === 0) return;

    window.speechSynthesis.cancel();
    appState.isPodcastPlaying = true;
    animateWaveform(true);

    const playBtn = document.getElementById('podcastPlayBtn');
    if (playBtn) playBtn.innerText = '⏸';

    let currentIdx = startIndex;
    function speakNext() {
        if (!appState.isPodcastPlaying || currentIdx >= script.length) {
            stopSpeechSynthesis();
            return;
        }
        const item = script[currentIdx];
        const utterance = new SpeechSynthesisUtterance(`${item.speaker || 'Host'}: ${item.text}`);
        utterance.rate = appState.podcastPlaybackSpeed || 1.0;
        utterance.onend = () => {
            currentIdx++;
            speakNext();
        };
        utterance.onerror = () => {
            stopSpeechSynthesis();
        };
        window.speechSynthesis.speak(utterance);
    }
    speakNext();
}

export function togglePodcastPlayback() {
    const audioEl = getPodcastAudioElement();
    const playBtn = document.getElementById('podcastPlayBtn');

    // If currently playing via speech synthesis, pause/stop it
    if (typeof window !== 'undefined' && window.speechSynthesis && window.speechSynthesis.speaking) {
        stopSpeechSynthesis();
        return;
    }

    const hasAudioSrc = Boolean(audioEl && audioEl.getAttribute('src') && audioEl.getAttribute('src').trim() !== '');

    if (audioEl && hasAudioSrc) {
        if (audioEl.paused) {
            audioEl.play().then(() => {
                appState.isPodcastPlaying = true;
                if (playBtn) playBtn.innerText = '⏸';
                animateWaveform(true);
            }).catch(() => {
                // If audio playback rejects (e.g. 404 or unplayable), seamlessly fallback to Web Speech API
                playSpeechSynthesisDialogue(0);
            });
        } else {
            audioEl.pause();
            appState.isPodcastPlaying = false;
            if (playBtn) playBtn.innerText = '▶';
            animateWaveform(false);
        }
    } else {
        // Fallback directly to Web Speech API dialogue synthesis
        if (appState.isPodcastPlaying) {
            stopSpeechSynthesis();
        } else {
            playSpeechSynthesisDialogue(0);
        }
    }
}

export function setPodcastSpeed(speed) {
    appState.podcastPlaybackSpeed = speed;
    const audioEl = getPodcastAudioElement();
    if (audioEl) {
        audioEl.playbackRate = speed;
    }
    ['10', '12', '15'].forEach(s => {
        const btn = document.getElementById(`speed${s}`);
        if (!btn) return;
        const matches = (speed === 1.0 && s === '10') || (speed === 1.25 && s === '12') || (speed === 1.5 && s === '15');
        if (matches) {
            btn.className = 'px-1.5 py-0.2 rounded bg-indigo-600 text-white cursor-pointer';
        } else {
            btn.className = 'px-1.5 py-0.2 rounded text-slate-600 hover:text-slate-900 cursor-pointer';
        }
    });
}

export function playPodcastFromIndex(idx) {
    const audioEl = getPodcastAudioElement();
    const hasAudioSrc = audioEl && audioEl.getAttribute('src');
    if (!hasAudioSrc) {
        playSpeechSynthesisDialogue(idx);
        return;
    }
    const script = getPodcastScriptForWeek(appState.activeTimeMachineWeek);
    const segment = script[idx];
    if (segment && segment.time) {
        const parts = segment.time.split(':');
        const secs = (parseInt(parts[0], 10) || 0) * 60 + (parseInt(parts[1], 10) || 0);
        audioEl.currentTime = secs;
    }
    if (audioEl.paused) {
        togglePodcastPlayback();
    }
}

export function toggleTranscriptModal() {
    const modal = document.getElementById(DOM_IDS.TRANSCRIPT_MODAL);
    if (!modal) return;
    const isHidden = modal.classList.contains('hidden');
    if (isHidden) {
        renderPodcastTranscript(appState.activeTimeMachineWeek);
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

export function renderPodcastTranscript(weekKey) {
    const container = getRequiredElement(DOM_IDS.PODCAST_TRANSCRIPT_CONTAINER, 'renderPodcastTranscript');
    if (!container) return;
    const script = getPodcastScriptForWeek(weekKey || appState.activeTimeMachineWeek);
    container.innerHTML = script.map((item, idx) => `
        <div onclick="playPodcastFromIndex(${idx})" class="p-3 rounded-xl border border-slate-200 hover:border-indigo-300 bg-slate-50/70 hover:bg-indigo-50/40 transition-all cursor-pointer space-y-1">
            <div class="flex items-center justify-between text-[11px]">
                <span class="font-bold text-indigo-900">${item.speaker || 'Host'}</span>
                <span class="font-mono text-slate-400">${item.time || '00:00'}</span>
            </div>
            <p class="text-xs text-slate-700 leading-relaxed">${item.text}</p>
        </div>
    `).join('');
}

export function copyPodcastScript() {
    const script = getPodcastScriptForWeek(appState.activeTimeMachineWeek);
    const text = script.map(s => `[${s.time || '00:00'}] ${s.speaker}: ${s.text}`).join('\n\n');
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text);
    }
}
