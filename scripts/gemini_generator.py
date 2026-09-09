import os
import sys
import io
import json
import base64
import logging
from datetime import datetime
from typing import TypedDict, Optional, List, Dict, Any, Tuple

import requests
import google.auth
import google.auth.transport.requests

from google import genai
from google.genai import types

from pydantic import BaseModel, Field

logger = logging.getLogger('gemini_generator')

class ToneSynthesis(BaseModel):
    executive: str = Field(description="60-80 word single-paragraph executive summary highlighting posture, velocity, and key decisions.")
    technical: str = Field(description="60-80 word single-paragraph engineering summary covering platform status, security assessors, and delivery milestones.")
    governance: str = Field(description="60-80 word single-paragraph commercial and governance summary detailing escalations and milestone verification.")

class Top3Item(BaseModel):
    num: int = Field(description="Priority order index (1, 2, or 3).")
    type: str = Field(description="Category type: 'decision', 'schedule', or 'win'.")
    tag: str = Field(description="Category label: '🚨 Immediate Executive Action', '⚡ Critical Schedule Alignment', or '🚀 Primary Delivery Win'.")
    ref: str = Field(description="Exact deliverable or milestone reference code taken strictly from the input data. Do not hallucinate.")
    title: str = Field(description="Concise factual title of the action item.")
    impact: str = Field(description="Direct impact statement.")
    action: str = Field(description="Specific actionable next step or decision required.")

class SleeperOutlier(BaseModel):
    ref: str = Field(description="Exact deliverable or milestone reference code from the input data that is at risk of turning red. Do not hallucinate.")
    title: str = Field(description="Factual deliverable name from the input data.")
    warning: str = Field(description="Operational rationale explaining why this item is at risk due to schedule compression, dependencies, or lead time.")

class ExecutiveSynthesisResult(BaseModel):
    synthesis: ToneSynthesis
    top3: List[Top3Item]
    sleeperOutlier: SleeperOutlier

class PodcastDialogueTurn(BaseModel):
    speaker: str = Field(description="Speaker name ('Alex' or 'Jordan').")
    role: str = Field(description="Speaker role title.")
    avatar: str = Field(description="Emoji avatar icon.")
    time: str = Field(description="Timestamp in format MM:SS.")
    text: str = Field(description="Spoken dialogue text.")

class PodcastScriptResponse(BaseModel):
    dialogue: List[PodcastDialogueTurn] = Field(description="Sequential list of 5 podcast dialogue turns.")

class ReportMetadataInspection(BaseModel):
    week_number: int = Field(description="The program or project reporting week number integer (e.g. 28, 29, 30).")
    week_label: str = Field(description="Standardized week label (e.g. 'Week 28').")
    report_date: str = Field(description="The formal reporting date in 'DD Mon YYYY' format (e.g. '14 Aug 2026').")
    title: str = Field(description="Report title or document headline found on the title slide or document header.")
    summary: str = Field(description="Brief 1-sentence summary of the report pack scope or period.")

def get_default_gemini_region(override: Optional[str] = None) -> str:
    """
    Dynamically resolves the active Vertex AI location for Gemini generation:
      1. Explicit argument override
      2. GEMINI_REGION environment variable (e.g. 'us', 'us-central1', 'australia-southeast1')
      3. GCP_REGION / GOOGLE_CLOUD_LOCATION environment variable
      4. System default fallback ('us' where gemini-3.5-flash multi-region endpoint is hosted)
    """
    return override or os.getenv("GEMINI_REGION") or os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_LOCATION") or "us"

def get_default_gemini_model(override: Optional[str] = None) -> str:
    """
    Dynamically resolves the active Gemini model name in order of precedence:
      1. Explicit argument override
      2. GEMINI_MODEL environment variable
      3. System default fallback ('gemini-3.5-flash')
    """
    return override or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

def get_gemini_client(location: Optional[str] = None) -> Optional[genai.Client]:
    """Initializes genai.Client with ADC Vertex AI priority and API Key fallback.
    
    Supports multi-region endpoints ('us', 'eu') with automatic .rep. hostname configuration.
    """
    project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    loc = get_default_gemini_region(location)
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    http_opts = None
    if loc in ['us', 'eu']:
        http_opts = types.HttpOptions(base_url=f"https://aiplatform.{loc}.rep.googleapis.com")
    elif loc == 'global':
        http_opts = types.HttpOptions(base_url="https://aiplatform.googleapis.com")
    
    # 1. Try Vertex AI with ADC if project is explicitly configured in environment
    if project:
        try:
            kwargs: Dict[str, Any] = {"vertexai": True, "project": project, "location": loc}
            if http_opts:
                kwargs["http_options"] = http_opts
            return genai.Client(**kwargs)
        except Exception as e:
            logger.warning(f"Vertex AI ADC initialization failed for region '{loc}': {e}")

    # 2. Try API Key if provided
    if api_key and api_key != "MY_GEMINI_API_KEY":
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            logger.warning(f"API Key Client initialization failed: {e}")

    # 3. Try ADC fallback with default project discovery
    try:
        from google.auth import default
        _, default_proj = default()
        if default_proj:
            kwargs = {"vertexai": True, "project": default_proj, "location": loc}
            if http_opts:
                kwargs["http_options"] = http_opts
            return genai.Client(**kwargs)
    except Exception:
        pass

    # 4. Default client probe
    try:
        return genai.Client()
    except Exception as e:
        logger.warning(f"Gemini client not configured or credentials missing: {e}")
        return None

def build_synthesis_prompt(metrics: Dict[str, Any], gap_close_plans: List[Dict[str, Any]]) -> str:
    """Builds prompt string from metrics and plans."""
    prompt_template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "exec_summary_prompt.md")
    
    if os.path.exists(prompt_template_path):
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    else:
        template = """You are the Principal Program Delivery Advisor for the leadership executive board.
Provide an exception-first executive briefing based on the following weekly metrics:
- Reporting Period: {{REPORT_WEEK}} (Ending {{REPORT_DATE}})
- Baseline: Compared against {{BASELINE_WEEK}} ({{BASELINE_DATE}})
- Overall Status: {{OVERALL_STATUS}}
- Commercial: {{COMMERCIAL_STATUS}}
- Milestone/IBR: {{IBR_STATUS}}
- ATO-C: {{ATO_STATUS}}
- Escalations: {{ESCALATIONS_COUNT}} items
- Active Plans: {{GAP_CLOSE_MOVEMENTS}}
- Total Risks: {{TOTAL_RISKS}}
- Inherent Avg: {{INHERENT_AVG_SCORE}} -> Residual Avg: {{RESIDUAL_AVG_SCORE}} (Delta {{DELTA_COMPRESSION}})
- Eventuated Issues: {{EVENTUATED_ISSUES_COUNT}} / Total Issues: {{TOTAL_ISSUES}}
"""

    plans_str = '\n'.join([
        f"- Plan #{p.get('num', idx+1)} ({p.get('ref', 'N/A')}) [{p.get('status', 'AMBER')}]: {p.get('title', '')} - Plan: {p.get('plan', '')} (Owner: {p.get('owner', 'TBD')}, Target: {p.get('target', 'TBD')})"
        for idx, p in enumerate(gap_close_plans)
    ])

    project_name = metrics.get('project_name') or 'Program Portfolio'
    project_title = metrics.get('project_title') or 'Delivery Governance'
    organization = metrics.get('organization') or 'Executive Board'

    replacements = {
        "{{PROJECT_NAME}}": str(project_name),
        "{{PROJECT_TITLE}}": str(project_title),
        "{{ORGANIZATION}}": str(organization),
        "{{REPORT_WEEK}}": str(metrics.get('report_week', 'Current Reporting Cycle')),
        "{{REPORT_DATE}}": str(metrics.get('report_date', datetime.now().strftime('%d %b %Y'))),
        "{{BASELINE_WEEK}}": str(metrics.get('baseline_week', 'Previous Reporting Cycle')),
        "{{BASELINE_DATE}}": str(metrics.get('baseline_date', 'Previous Cycle')),
        "{{OVERALL_STATUS}}": str(metrics.get('overall_status', 'AMBER (Stable)')),
        "{{COMMERCIAL_STATUS}}": str(metrics.get('commercial_status', 'ON TRACK')),
        "{{IBR_STATUS}}": str(metrics.get('ibr_status', 'IN PROGRESS')),
        "{{ATO_STATUS}}": str(metrics.get('ato_status', 'IN PROGRESS')),
        "{{ESCALATIONS_COUNT}}": str(metrics.get('escalations_count', '0')),
        "{{GAP_CLOSE_MOVEMENTS}}": plans_str if plans_str else 'No active plan movements reported.',
        "{{TOTAL_RISKS}}": str(metrics.get('total_risks', '0')),
        "{{INHERENT_AVG_SCORE}}": str(metrics.get('inherent_avg_score', '0.0')),
        "{{RESIDUAL_AVG_SCORE}}": str(metrics.get('residual_avg_score', '0.0')),
        "{{DELTA_COMPRESSION}}": str(metrics.get('delta_compression', '0.0')),
        "{{EVENTUATED_ISSUES_COUNT}}": str(metrics.get('eventuated_issues_count', '0')),
        "{{TOTAL_ISSUES}}": str(metrics.get('total_issues', '0'))
    }

    prompt = template
    for key, val in replacements.items():
        prompt = prompt.replace(key, val)

    return prompt

def generate_executive_synthesis(
    metrics: Dict[str, Any],
    gap_close_plans: List[Dict[str, Any]],
    model: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    """Generates structured executive decision synthesis using dynamic Gemini model."""
    active_model = get_default_gemini_model(model)
    client = get_gemini_client(location=location)
    if not client:
        raise RuntimeError("Gemini Client could not be initialized. Please configure Google Cloud ADC or GEMINI_API_KEY in .env.")

    prompt = build_synthesis_prompt(metrics, gap_close_plans)
    
    try:
        response = client.models.generate_content(
            model=active_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExecutiveSynthesisResult,
                temperature=0.2
            )
        )
    except Exception as e:
        loc = get_default_gemini_region(location)
        if "404" in str(e) and loc != 'us':
            logger.warning(f"Model '{active_model}' not found in region '{loc}'. Retrying on 'us' multi-region endpoint...")
            fallback_client = get_gemini_client(location='us')
            if not fallback_client:
                raise
            response = fallback_client.models.generate_content(
                model=active_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExecutiveSynthesisResult,
                    temperature=0.2
                )
            )
        else:
            raise

    try:
        result = json.loads(response.text)
        result['generatedBy'] = active_model
        return result
    except Exception as e:
        logger.error(f"Failed to parse JSON output from Gemini: {e}\nRaw response: {response.text}")
        raise ValueError(f"Invalid JSON output received from {active_model}: {e}")

def upload_bytes_to_gcs(
    data_bytes: bytes,
    bucket_name: str,
    blob_name: str,
    content_type: str = "audio/mpeg"
) -> bool:
    """Uploads binary data directly to Google Cloud Storage via REST API using ADC credentials."""
    try:
        creds, _ = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        quota_project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "monaro-risk-dev"
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": content_type,
            "X-Goog-User-Project": quota_project
        }
        url = f"https://storage.googleapis.com/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name={blob_name}"
        r = requests.post(url, headers=headers, data=data_bytes, timeout=30)
        if r.status_code in [200, 201]:
            logger.info(f"Successfully uploaded {len(data_bytes)} bytes to gs://{bucket_name}/{blob_name}")
            return True
        logger.warning(f"GCS upload failed (status {r.status_code}): {r.text[:200]}")
        return False
    except Exception as e:
        logger.warning(f"GCS upload encountered error for {blob_name}: {e}")
        return False


def get_turn_audio_duration(audio_bytes: bytes) -> float:
    """Calculates spoken duration in seconds for an MP3 audio segment."""
    try:
        import mutagen
        from mutagen.mp3 import MP3
        a = MP3(io.BytesIO(audio_bytes))
        if a.info and getattr(a.info, 'length', None):
            return float(a.info.length)
    except Exception:
        pass
    if len(audio_bytes) > 0:
        return max(1.0, len(audio_bytes) / 4000.0)
    return 1.0


def synthesize_podcast_audio(
    podcast_script: List[Dict[str, Any]],
    output_audio_path: Optional[str] = None,
    language_code: str = "en-AU",
    speaking_rate: float = 1.0,
    gcs_bucket: Optional[str] = None,
    gcs_blob_name: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], Optional[bytes], Optional[float]]:
    """
    Synthesizes multi-speaker podcast audio using Google Cloud Text-to-Speech Chirp 3 HD.
    Voices:
      - Alex: en-AU-Chirp3-HD-Puck (fallback: en-AU-Neural2-B / en-US-Journey-D)
      - Jordan: en-AU-Chirp3-HD-Aoede (fallback: en-AU-Neural2-A / en-US-Journey-F)
    
    Dynamically recalculates each turn's spoken duration and start timestamp ('time' field),
    stitches turns with natural micro-pauses (300ms silence), saves to output_audio_path,
    and optionally uploads to GCS bucket.

    Returns (updated_script, audio_bytes, total_duration_seconds).
    """
    if not podcast_script:
        return [], None, 0.0

    try:
        creds, _ = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
    except Exception as e:
        logger.warning(f"Could not initialize Google Cloud auth for audio synthesis: {e}")
        return podcast_script, None, 0.0

    quota_project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or "monaro-risk-dev"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json; charset=utf-8",
        "X-Goog-User-Project": quota_project
    }

    voice_map = {
        "alex": {
            "primary": f"{language_code}-Chirp3-HD-Puck" if language_code == "en-AU" else "en-US-Journey-D",
            "fallback": f"{language_code}-Neural2-B" if language_code == "en-AU" else "en-US-Journey-D"
        },
        "jordan": {
            "primary": f"{language_code}-Chirp3-HD-Aoede" if language_code == "en-AU" else "en-US-Journey-F",
            "fallback": f"{language_code}-Neural2-A" if language_code == "en-AU" else "en-US-Journey-F"
        }
    }

    audio_chunks: List[bytes] = []
    updated_script: List[Dict[str, Any]] = []
    elapsed_seconds: float = 0.0

    for idx, turn in enumerate(podcast_script):
        turn_copy = dict(turn)
        spk = str(turn.get("speaker", "Alex")).lower()
        text = str(turn.get("text", "")).strip()
        if not text:
            continue

        spk_config = voice_map.get("alex" if "alex" in spk else "jordan", voice_map["alex"])
        target_voice = spk_config["primary"]

        tts_payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": language_code,
                "name": target_voice
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": speaking_rate,
                "pitch": 0.0
            }
        }

        chunk_bytes = None
        try:
            r = requests.post(
                "https://texttospeech.googleapis.com/v1/text:synthesize",
                headers=headers,
                json=tts_payload,
                timeout=20
            )
            if r.status_code == 200:
                chunk_bytes = base64.b64decode(r.json().get("audioContent", ""))
            else:
                logger.warning(f"Chirp3 HD synthesis failed ({r.status_code}): {r.text[:150]}. Trying Neural2 fallback...")
                fallback_voice = spk_config["fallback"]
                tts_payload["voice"]["name"] = fallback_voice
                r_fb = requests.post(
                    "https://texttospeech.googleapis.com/v1/text:synthesize",
                    headers=headers,
                    json=tts_payload,
                    timeout=20
                )
                if r_fb.status_code == 200:
                    chunk_bytes = base64.b64decode(r_fb.json().get("audioContent", ""))
        except Exception as err:
            logger.warning(f"Error during turn {idx+1} audio synthesis: {err}")

        if chunk_bytes:
            audio_chunks.append(chunk_bytes)
            turn_dur = get_turn_audio_duration(chunk_bytes)
        else:
            turn_dur = max(2.0, len(text.split()) / 2.3)

        mins = int(elapsed_seconds // 60)
        secs = int(elapsed_seconds % 60)
        turn_copy["time"] = f"{mins}:{secs:02d}"
        updated_script.append(turn_copy)

        elapsed_seconds += turn_dur + 0.30

    if not audio_chunks:
        logger.warning("No audio chunks synthesized successfully.")
        return updated_script, None, 0.0

    combined_mp3 = b"".join(audio_chunks)
    total_dur = get_turn_audio_duration(combined_mp3)

    if output_audio_path:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)
            with open(output_audio_path, "wb") as f:
                f.write(combined_mp3)
            logger.info(f"Saved executive podcast audio ({len(combined_mp3)} bytes, {total_dur:.1f}s) to {output_audio_path}")
        except Exception as e:
            logger.error(f"Failed to write audio file to {output_audio_path}: {e}")

    # GCS Persistence
    target_bucket = gcs_bucket or os.getenv("DATA_BUCKET") or f"{quota_project}-data"
    target_blob = gcs_blob_name
    if not target_blob and output_audio_path:
        base_name = os.path.basename(output_audio_path)
        proj_match = os.path.basename(os.path.dirname(os.path.abspath(output_audio_path)))
        if proj_match in ["monaro", "sample"]:
            target_blob = f"{proj_match}/{base_name}"
        else:
            target_blob = f"assets/{base_name}"

    if target_bucket and target_blob:
        upload_bytes_to_gcs(combined_mp3, target_bucket, target_blob, content_type="audio/mpeg")

    return updated_script, combined_mp3, total_dur

def generate_multispeaker_podcast(
    metrics: Dict[str, Any],
    synthesis_result: Dict[str, Any],
    model: Optional[str] = None,
    location: Optional[str] = None,
    audio_out_path: Optional[str] = None,
    language_code: str = "en-AU"
) -> List[Dict[str, Any]]:
    """Generates dual-host dialogue transcript and studio audio between Alex and Jordan using Gemini and Cloud TTS."""
    active_model = get_default_gemini_model(model)
    client = get_gemini_client(location=location)
    if not client:
        raise RuntimeError("Gemini Client could not be initialized. Please configure Google Cloud ADC or GEMINI_API_KEY in .env.")

    week_label = metrics.get('report_week', 'Current Reporting Cycle')
    report_date = metrics.get('report_date', datetime.now().strftime('%d %b %Y'))

    prompt = f"""Generate a professional, high-impact 90-second conversational executive podcast briefing between two hosts:
- Alex (Host / Program Delivery Analyst): Neutral, crisp, direct, executive delivery focus.
- Jordan (Co-Host / Technical Director): Authoritative, technical, solutions-focused.

Reporting Week: {week_label} ({report_date})
Executive Summary: {synthesis_result.get('synthesis', {}).get('executive', '')}
Technical Assessment: {synthesis_result.get('synthesis', {}).get('technical', '')}
Governance Summary: {synthesis_result.get('synthesis', {}).get('governance', '')}
Top 3 Attention Items: {json.dumps(synthesis_result.get('top3', []))}
Sleeper Outlier: {json.dumps(synthesis_result.get('sleeperOutlier', {}))}

Return STRICT JSON as an object containing an array of 5 structured dialogue turns:
1. Alex: Welcome to the Executive Briefing for {week_label} ending {report_date}, framing executive posture and core delivery focus.
2. Jordan: Technical Director analysis on milestone velocity, engineering baseline, and risk compression metrics.
3. Alex: Deep dive on the primary Top Attention item and critical-path decision required.
4. Jordan: Technical mitigation on secondary priority, engineering interconnects, and sleeper outlier proactively treated.
5. Alex: Summary of commercial, ATO accreditation, and governance posture, closing with executive action items.

Schema:
{{
  "dialogue": [
    {{"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:00", "text": "Welcome to the Executive Briefing for {week_label}..."}},
    {{"speaker": "Jordan", "role": "Technical Director", "avatar": "🤖", "time": "0:18", "text": "Thank you Alex..."}},
    {{"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "0:36", "text": "..."}},
    {{"speaker": "Jordan", "role": "Technical Director", "avatar": "🤖", "time": "0:54", "text": "..."}},
    {{"speaker": "Alex", "role": "Program Analyst", "avatar": "🎙️", "time": "1:15", "text": "..."}}
  ]
}}
"""

    try:
        response = client.models.generate_content(
            model=active_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PodcastScriptResponse,
                temperature=0.3
            )
        )
    except Exception as e:
        loc = get_default_gemini_region(location)
        if "404" in str(e):
            logger.warning(f"Model '{active_model}' in region '{loc}' returned 404. Probing 'us' multi-region endpoint...")
            try:
                fallback_client = get_gemini_client(location='us')
                if fallback_client:
                    response = fallback_client.models.generate_content(
                        model=active_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=PodcastScriptResponse,
                            temperature=0.3
                        )
                    )
            except Exception as e2:
                logger.warning(f"Fallback to 'us' failed ({e2}). Retrying with 'gemini-2.5-flash' in 'us-central1'...")
                fb_client_2 = get_gemini_client(location='us-central1')
                if not fb_client_2:
                    raise
                response = fb_client_2.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=PodcastScriptResponse,
                        temperature=0.3
                    )
                )
        else:
            raise

    try:
        raw = json.loads(response.text)
        if isinstance(raw, dict) and 'dialogue' in raw:
            script = raw['dialogue']
        elif isinstance(raw, list):
            script = raw
        else:
            raise ValueError(f"Unexpected JSON format: {raw}")
    except Exception as e:
        logger.error(f"Failed to parse podcast script JSON: {e}\nRaw response: {response.text}")
        raise ValueError(f"Invalid podcast script JSON from {active_model}: {e}")

    # Synthesize multi-speaker audio if audio output path requested
    if audio_out_path:
        try:
            script, _, _ = synthesize_podcast_audio(
                podcast_script=script,
                output_audio_path=audio_out_path,
                language_code=language_code
            )
        except Exception as e:
            logger.warning(f"Audio synthesis encountered error: {e}")

    return script

def inspect_report_with_gemini(
    file_content_or_path: Any,
    file_name: str = "",
    mime_type: str = "application/pdf",
    model: Optional[str] = None,
    location: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Inspects report content or document files using Gemini Multimodal AI to extract
    the reporting week number, formal date, and title from cover slides or document headers.
    """
    active_model = get_default_gemini_model(model)
    client = get_gemini_client(location=location)
    if not client:
        return None

    try:
        contents = []
        prompt_text = (
            f"Inspect the provided report document (filename: '{file_name}'). "
            "Extract the exact program/project reporting week number (as an integer), "
            "the formal reporting date (formatted as 'DD Mon YYYY', e.g. '14 Aug 2026'), "
            "the document title, and a brief 1-sentence summary of the reporting period. "
            "If the week number is not explicitly stated in text, infer it from the date or context."
        )

        if isinstance(file_content_or_path, str) and os.path.exists(file_content_or_path):
            with open(file_content_or_path, 'rb') as f:
                raw_bytes = f.read()
            contents.append(types.Part.from_bytes(data=raw_bytes, mime_type=mime_type))
        elif isinstance(file_content_or_path, bytes):
            contents.append(types.Part.from_bytes(data=file_content_or_path, mime_type=mime_type))
        elif isinstance(file_content_or_path, str) and len(file_content_or_path) > 0:
            contents.append(file_content_or_path)

        contents.append(prompt_text)

        try:
            response = client.models.generate_content(
                model=active_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ReportMetadataInspection,
                    temperature=0.1
                )
            )
        except Exception as e:
            loc = get_default_gemini_region(location)
            if "404" in str(e) and loc not in ['us', 'global']:
                logger.warning(f"Model '{active_model}' not found in region '{loc}'. Retrying on multi-region 'us' endpoint...")
                fallback_client = get_gemini_client(location='us')
                if not fallback_client:
                    raise
                response = fallback_client.models.generate_content(
                    model=active_model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ReportMetadataInspection,
                        temperature=0.1
                    )
                )
            else:
                raise

        if response.text:
            result = json.loads(response.text)
            result['inspectedBy'] = active_model
            return result
    except Exception as e:
        logger.warning(f"Gemini multimodal report inspection encountered an error: {e}")
        return None

    return None

