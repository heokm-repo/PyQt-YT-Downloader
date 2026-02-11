"""
yt-dlp.exe subprocess 래퍼
- yt-dlp.exe를 외부 프로세스로 실행
- Python API와 동일한 인터페이스 제공
- stdout 파싱을 통한 진행률 모니터링
"""
import subprocess
import json
import re
import os
from typing import Dict, Callable, Optional, Tuple, List
from utils.logger import log
from constants import YTDLP_TIMEOUT, YTDLP_RETRIES, DEFAULT_ENCODING


class YtDlpWrapper:
    """yt-dlp.exe를 Python API처럼 사용할 수 있게 래핑하는 클래스"""
    
    def __init__(self, ytdlp_path: str, ffmpeg_path: Optional[str] = None):
        """
        Args:
            ytdlp_path: yt-dlp.exe 경로
            ffmpeg_path: ffmpeg.exe 경로 (선택)
        """
        self.ytdlp_path = ytdlp_path
        self.ffmpeg_path = ffmpeg_path
        
        # 진행률 파싱용 정규식 패턴
        # [download]  45.2% of 10.5MiB at 2.3MiB/s ETA 00:03
        self.progress_pattern = re.compile(
            r'\[download\]\s+(?P<percent>[\d.]+)%\s+of\s+(?P<total>[\d.]+)(?P<total_unit>\w+)'
            r'(?:\s+at\s+(?P<speed>[\d.]+)(?P<speed_unit>\w+)/s)?'
            r'(?:\s+ETA\s+(?P<eta>[\d:]+))?'
        )
        
        # [download] Destination: filename.mp4
        self.destination_pattern = re.compile(r'\[download\] Destination: (.+)')
        
        # [download] 100% of 10.5MiB in 00:04
        self.complete_pattern = re.compile(r'\[download\] 100%')
    
    def download(self, url: str, options: Dict, progress_hook: Callable) -> Tuple[bool, str]:
        """
        영상 다운로드 (기존 yt_dlp.YoutubeDL().download()와 동일한 인터페이스)
        
        Args:
            url: 다운로드 URL
            options: yt-dlp 옵션 딕셔너리
            progress_hook: 진행률 콜백 함수
        
        Returns:
            (성공 여부, 에러 메시지)
        """
        try:
            # 옵션을 CLI 인자로 변환
            args = self._build_command(url, options)
            
            log.info(f"Running yt-dlp: {' '.join(args)}")
            
            # subprocess 실행
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding=DEFAULT_ENCODING,
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 진행률 추적을 위한 변수
            current_file = None
            fragments = []  # [{'type': 'video', 'total': 1000, 'downloaded': 500}, ...]
            current_fragment = None
            last_progress = {}
            
            # stdout 실시간 파싱
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                
                line = line.strip()
                
                # Destination 파싱 (새 fragment 시작)
                dest_match = self.destination_pattern.search(line)
                if dest_match:
                    current_file = dest_match.group(1)
                    log.info(f"Downloading to: {current_file}")
                    
                    # 새 fragment 준비
                    current_fragment = {
                        'type': 'video' if 'f' in current_file and 'mp4' in current_file else 'audio',
                        'total': 0,
                        'downloaded': 0
                    }
                
                # 진행률 파싱
                progress_data = self._parse_progress(line)
                if progress_data and current_fragment is not None:
                    # 현재 fragment 정보 업데이트
                    if current_fragment['total'] == 0:
                        current_fragment['total'] = progress_data['total_bytes']
                        fragments.append(current_fragment)
                    
                    current_fragment['downloaded'] = progress_data['downloaded_bytes']
                    
                    # 전체 진행률 계산
                    total_bytes = sum(f['total'] for f in fragments)
                    downloaded_bytes = sum(f['downloaded'] for f in fragments)
                    
                    if total_bytes > 0:
                        combined_progress = {
                            'status': 'downloading',
                            'downloaded_bytes': downloaded_bytes,
                            'total_bytes': total_bytes,
                            'speed': progress_data.get('speed'),
                            'eta': progress_data.get('eta'),
                            '_percent_str': f'{downloaded_bytes * 100 / total_bytes:.1f}%',
                        }
                        
                        # 중복 진행률 호출 방지
                        if combined_progress != last_progress:
                            progress_hook(combined_progress)
                            last_progress = combined_progress
                
                # 완료 감지
                if self.complete_pattern.search(line):
                    log.info("Download complete")
                    progress_hook({'status': 'finished', 'filename': current_file})
            
            # 프로세스 종료 대기
            process.wait()
            
            # stderr 확인
            stderr = process.stderr.read()
            if stderr:
                log.warning(f"yt-dlp stderr: {stderr}")
            
            if process.returncode != 0:
                error_msg = f"yt-dlp exited with code {process.returncode}"
                if stderr:
                    error_msg += f": {stderr}"
                log.error(error_msg)
                return False, error_msg
            
            return True, "Download complete"
            
        except subprocess.SubprocessError as e:
            error_msg = f"Subprocess error: {e}"
            log.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            log.error(error_msg)
            return False, error_msg
    
    def extract_info(self, url: str, download: bool = False, options: Optional[Dict] = None) -> Tuple[Optional[Dict], bool]:
        """
        메타데이터 추출 (기존 yt_dlp.YoutubeDL().extract_info()와 동일한 인터페이스)
        
        Args:
            url: YouTube URL
            download: 다운로드 여부 (False면 메타데이터만)
            options: 추가 옵션
        
        Returns:
            (메타데이터 딕셔너리, 성공 여부)
        """
        try:
            # --dump-json으로 메타데이터 추출
            args = [self.ytdlp_path, '--dump-json', '--no-warnings']
            
            # 옵션 적용
            if options:
                if options.get('extract_flat'):
                    args.append('--flat-playlist')
                
                if options.get('noplaylist'):
                    args.append('--no-playlist')
                
                # format 옵션 추가 (크기 추정을 위해)
                if 'format' in options:
                    args.extend(['--format', options['format']])
            
            args.append(url)
            
            log.info(f"Extracting info: {' '.join(args)}")
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding=DEFAULT_ENCODING,
                errors='replace',
                timeout=YTDLP_TIMEOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                log.error(f"extract_info failed: {result.stderr}")
                return None, False
            
            # JSON 파싱
            # --dump-json은 여러 줄의 JSON을 출력할 수 있음 (플레이리스트)
            lines = result.stdout.strip().split('\n')
            
            if len(lines) == 1:
                # 단일 영상
                info = json.loads(lines[0])
                return info, True
            else:
                # 플레이리스트 (여러 JSON)
                entries = []
                for line in lines:
                    if line.strip():
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                
                if entries:
                    # 첫 번째 항목을 기본으로, entries 추가
                    info = entries[0] if len(entries) == 1 else {
                        'entries': entries,
                        '_type': 'playlist'
                    }
                    return info, True
                else:
                    return None, False
            
        except subprocess.TimeoutExpired:
            log.error("extract_info timeout")
            return None, False
        except json.JSONDecodeError as e:
            log.error(f"JSON parse error: {e}")
            return None, False
        except Exception as e:
            log.error(f"extract_info error: {e}")
            return None, False
    
    def _parse_progress(self, line: str) -> Optional[Dict]:
        """
        yt-dlp stdout에서 진행률 파싱
        
        Args:
            line: stdout 라인
        
        Returns:
            진행률 딕셔너리 (기존 progress_hook 형식)
            {
                'status': 'downloading',
                'downloaded_bytes': 4744806,
                'total_bytes': 11010048,
                'speed': 2411724.8,
                'eta': 3,
                '_percent_str': '45.2%',
                '_total_bytes_str': '10.5MiB',
                '_speed_str': '2.3MiB/s'
            }
        """
        match = self.progress_pattern.search(line)
        
        if not match:
            return None
        
        percent = float(match.group('percent'))
        total_size = float(match.group('total'))
        total_unit = match.group('total_unit')
        speed_str = match.group('speed')
        speed_unit = match.group('speed_unit')
        eta_str = match.group('eta')
        
        # 단위 변환 (MiB, GiB 등 -> bytes)
        total_bytes = self._convert_to_bytes(total_size, total_unit)
        downloaded_bytes = int(total_bytes * percent / 100)
        
        # 속도 변환
        speed = None
        if speed_str and speed_unit:
            speed = self._convert_to_bytes(float(speed_str), speed_unit)
        
        # ETA 변환 (00:03 -> 3초)
        eta = None
        if eta_str:
            eta = self._parse_eta(eta_str)
        
        return {
            'status': 'downloading',
            'downloaded_bytes': downloaded_bytes,
            'total_bytes': total_bytes,
            'speed': speed,
            'eta': eta,
            '_percent_str': f'{percent}%',
            '_total_bytes_str': f'{total_size}{total_unit}',
            '_speed_str': f'{speed_str}{speed_unit}/s' if speed_str else None
        }
    
    def _convert_to_bytes(self, size: float, unit: str) -> int:
        """
        크기 단위를 bytes로 변환
        
        Args:
            size: 크기 (숫자)
            unit: 단위 (KiB, MiB, GiB, KB, MB, GB 등)
        
        Returns:
            bytes
        """
        # Binary units (KiB, MiB, GiB)
        if 'iB' in unit:
            unit = unit.replace('iB', '')
            multiplier = 1024
        # Decimal units (KB, MB, GB)
        else:
            unit = unit.replace('B', '')
            multiplier = 1000
        
        unit_map = {
            'K': multiplier,
            'M': multiplier ** 2,
            'G': multiplier ** 3,
            'T': multiplier ** 4,
        }
        
        return int(size * unit_map.get(unit, 1))
    
    def _parse_eta(self, eta_str: str) -> int:
        """
        ETA 문자열을 초로 변환
        
        Args:
            eta_str: "00:03" 또는 "01:23:45"
        
        Returns:
            초
        """
        parts = eta_str.split(':')
        
        if len(parts) == 2:
            # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            return 0
    
    def _build_command(self, url: str, options: Dict) -> List[str]:
        """
        Python dict 옵션을 CLI 인자로 변환
        
        Args:
            url: 다운로드 URL
            options: yt-dlp 옵션 딕셔너리
        
        Returns:
            CLI 인자 리스트
        """
        args = [self.ytdlp_path]
        
        # 출력 템플릿
        if 'outtmpl' in options:
            args.extend(['--output', options['outtmpl']])
        
        # 포맷
        if 'format' in options:
            args.extend(['--format', options['format']])
        
        # 병합 포맷
        if 'merge_output_format' in options:
            args.extend(['--merge-output-format', options['merge_output_format']])
        
        # FFmpeg 경로
        if 'ffmpeg_location' in options:
            args.extend(['--ffmpeg-location', options['ffmpeg_location']])
        elif self.ffmpeg_path:
            args.extend(['--ffmpeg-location', self.ffmpeg_path])
        
        # 플레이리스트
        if options.get('noplaylist'):
            args.append('--no-playlist')
        
        # 오디오 추출
        if options.get('extract_audio'):
            args.append('--extract-audio')
            
            if 'audio_format' in options:
                args.extend(['--audio-format', options['audio_format']])
        
        # 후처리 인자 (postprocessor_args)
        if 'postprocessor_args' in options:
            pp_args = options['postprocessor_args']
            if 'ffmpeg' in pp_args:
                ffmpeg_args = pp_args['ffmpeg']
                # ['-af', 'loudnorm=...'] -> '--postprocessor-args', 'ffmpeg:-af loudnorm=...'
                i = 0
                while i < len(ffmpeg_args):
                    arg = ffmpeg_args[i]
                    if i + 1 < len(ffmpeg_args):
                        value = ffmpeg_args[i + 1]
                        args.extend(['--postprocessor-args', f'ffmpeg:{arg} {value}'])
                        i += 2
                    else:
                        args.extend(['--postprocessor-args', f'ffmpeg:{arg}'])
                        i += 1
        
        # 동시 다운로드 (가속)
        if 'concurrent_fragment_downloads' in options:
            args.extend(['--concurrent-fragments', str(options['concurrent_fragment_downloads'])])
        
        # 덮어쓰기
        if options.get('overwrites'):
            args.append('--force-overwrites')
        
        # 기타 기본 옵션
        args.append('--no-warnings')
        
        # 이어받기 관련 옵션
        args.append('--continue')  # 이어받기 기능 (.part 파일 사용)
        args.append('--fragment-retries')  # fragment 재시도
        args.append(YTDLP_RETRIES)  # 최대 10회 재시도
        
        # URL 추가
        args.append(url)
        
        return args
