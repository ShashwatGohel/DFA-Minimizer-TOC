import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Tuple, List

from dfa import DFA
from nfa import NFA
from minimization import minimize_dfa_table_filling
from arden import dfa_to_regex_arden

ROOT = Path('.')
TEMPLATES_DIR = ROOT / 'templates'
STATIC_DIR = ROOT / 'static'

CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml; charset=utf-8',
    '.ico': 'image/x-icon'
}


def _escape_xml(text: str) -> str:
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def _data_url(svg: str) -> str:
    return 'data:image/svg+xml;utf8,' + urllib.parse.quote(svg)


def _layout_states(states: List[str], width: int, height: int) -> Dict[str, Tuple[float, float]]:
    import math
    n = max(1, len(states))
    cx, cy = width * 0.5, height * 0.55
    r = max(40.0, min(width, height) * 0.32)
    positions: Dict[str, Tuple[float, float]] = {}
    for i, s in enumerate(states):
        angle = 2 * math.pi * i / n
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        positions[s] = (x, y)
    return positions


def _arrow_marker_defs() -> str:
    return (
        '<defs>'
        '  <filter id="nodeShadow" x="-50%" y="-50%" width="200%" height="200%">'
        '    <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#000" flood-opacity="0.35"/>'
        '  </filter>'
        '  <filter id="labelShadow" x="-50%" y="-50%" width="200%" height="200%">'
        '    <feDropShadow dx="0" dy="2" stdDeviation="1.5" flood-color="#000" flood-opacity="0.35"/>'
        '  </filter>'
        '  <marker id="arrow-blue" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '    <path d="M 0 0 L 10 5 L 0 10 z" fill="#4a6fa5"></path>'
        '  </marker>'
        '  <marker id="arrow-green" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '    <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981"></path>'
        '  </marker>'
        '  <marker id="arrow-red" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '    <path d="M 0 0 L 10 5 L 0 10 z" fill="#ff0000"></path>'
        '  </marker>'
        '</defs>'
    )


def _group_edge_labels(transitions: Dict[Tuple[str, str], str]) -> Dict[Tuple[str, str], List[str]]:
    edge_labels: Dict[Tuple[str, str], List[str]] = {}
    for (u, a), v in transitions.items():
        edge_labels.setdefault((u, v), []).append(str(a))
    return edge_labels


def generate_dfa_svg(dfa: DFA, title: str = '') -> str:
    width, height = 1000, 600
    positions = _layout_states(sorted(list(dfa.states)), width, height)
    start = dfa.start_state
    accept = set(dfa.accept_states)

    edge_labels = _group_edge_labels(dfa.transitions)
    bidir = set()
    for (u, v) in list(edge_labels.keys()):
        if (v, u) in edge_labels and u != v:
            bidir.add((u, v))
            bidir.add((v, u))

    # Styling
    title_lower = (title or '').lower()
    stroke_color = '#10b981' if 'minimized' in title_lower else '#4a6fa5'
    marker_id = 'arrow-green' if 'minimized' in title_lower else 'arrow-blue'

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg.append(_arrow_marker_defs())
    if title:
        svg.append(f'<text x="20" y="40" fill="#e0e0e0" font-size="22" font-family="Arial" font-weight="bold">{_escape_xml(title)}</text>')
    svg.append('<rect x="0" y="0" width="100%" height="100%" fill="#1e1e1e"/>')

    R = 26.0
    for (u, v), labels in edge_labels.items():
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        label_text = ','.join(sorted(set(labels)))
        if u == v:
            loop_r = 40
            svg.append(
                f'<path d="M {x1} {y1-loop_r} c -44 -42, 44 -42, 0 0" fill="none" stroke="{stroke_color}" stroke-width="2.6" marker-end="url(#{marker_id})"/>'
            )
            lw = max(30.0, len(label_text) * 7.5 + 14)
            svg.append(f'<rect x="{x1 - lw/2:.2f}" y="{y1 - loop_r - 30:.2f}" width="{lw:.2f}" height="20" rx="7" ry="7" fill="#2d2d2d" stroke="#444" filter="url(#labelShadow)"/>'
                       )
            svg.append(f'<text x="{x1:.2f}" y="{y1 - loop_r - 15:.2f}" fill="#e5e7eb" font-size="13" text-anchor="middle" font-family="Arial">{_escape_xml(label_text)}</text>')
        else:
            import math
            dx, dy = x2 - x1, y2 - y1
            dist = max(1e-6, math.hypot(dx, dy))
            ux, uy = dx / dist, dy / dist
            sx, sy = x1 + ux * R, y1 + uy * R
            ex, ey = x2 - ux * R, y2 - uy * R
            nx, ny = -uy, ux
            curve_mag = (26 if (u, v) in bidir else 14)
            curve = curve_mag * (1 if u < v else -1)
            cx, cy = (sx + ex) / 2 + nx * curve, (sy + ey) / 2 + ny * curve
            svg.append(
                f'<path d="M {sx:.2f} {sy:.2f} Q {cx:.2f} {cy:.2f} {ex:.2f} {ey:.2f}" fill="none" stroke="{stroke_color}" stroke-width="2.6" marker-end="url(#{marker_id})" />'
            )
            lx, ly = (sx + ex) / 2 + nx * (curve + 0), (sy + ey) / 2 + ny * (curve + 0)
            lw = max(30.0, len(label_text) * 7.5 + 14)
            svg.append(f'<rect x="{lx - lw/2:.2f}" y="{ly - 18:.2f}" width="{lw:.2f}" height="20" rx="7" ry="7" fill="#2d2d2d" stroke="#444" filter="url(#labelShadow)"/>')
            svg.append(f'<text x="{lx:.2f}" y="{ly - 4:.2f}" fill="#e5e7eb" font-size="13" text-anchor="middle" font-family="Arial">{_escape_xml(label_text)}</text>')

    for s, (x, y) in positions.items():
        is_accept = s in accept
        svg.append(f'<circle cx="{x}" cy="{y}" r="26" fill="#ffffff" stroke="{stroke_color}" stroke-width="2.6" filter="url(#nodeShadow)"/>')
        if is_accept:
            svg.append(f'<circle cx="{x}" cy="{y}" r="21" fill="none" stroke="{stroke_color}" stroke-width="2.6"/>')
        svg.append(f'<text x="{x}" y="{y+5}" fill="#111827" font-size="15" text-anchor="middle" font-family="Arial" font-weight="bold">{_escape_xml(str(s))}</text>')
        if s == start:
            svg.append(f'<line x1="{x-72}" y1="{y}" x2="{x-29}" y2="{y}" stroke="{stroke_color}" stroke-width="2.6" marker-end="url(#{marker_id})" />')

    svg.append('</svg>')
    return _data_url(''.join(svg))


def generate_nfa_svg(nfa: 'NFA', title: str = '') -> str:
    width, height = 1000, 600
    positions = _layout_states(sorted(list(nfa.states)), width, height)
    start = nfa.start_state
    accept = set(nfa.accept_states)

    edge_labels: Dict[Tuple[str, str], List[str]] = {}
    for (u, a), targets in nfa.transitions.items():
        for v in targets:
            edge_labels.setdefault((u, v), []).append(str(a))
    bidir = set()
    for (u, v) in list(edge_labels.keys()):
        if (v, u) in edge_labels and u != v:
            bidir.add((u, v)); bidir.add((v, u))

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg.append(_arrow_marker_defs())
    if title:
        svg.append(f'<text x="20" y="40" fill="#e0e0e0" font-size="22" font-family="Arial" font-weight="bold">{_escape_xml(title)}</text>')
    svg.append('<rect x="0" y="0" width="100%" height="100%" fill="#1e1e1e"/>')

    stroke_color = '#4a6fa5'
    marker_id = 'arrow-blue'
    R = 26.0
    for (u, v), labels in edge_labels.items():
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        label_text = ','.join(sorted(set(labels)))
        if u == v:
            loop_r = 40
            svg.append(f'<path d="M {x1} {y1-loop_r} c -44 -42, 44 -42, 0 0" fill="none" stroke="{stroke_color}" stroke-width="2.6" marker-end="url(#{marker_id})"/>')
            lw = max(30.0, len(label_text) * 7.5 + 14)
            svg.append(f'<rect x="{x1 - lw/2:.2f}" y="{y1 - loop_r - 30:.2f}" width="{lw:.2f}" height="20" rx="7" ry="7" fill="#2d2d2d" stroke="#444" filter="url(#labelShadow)"/>')
            svg.append(f'<text x="{x1:.2f}" y="{y1 - loop_r - 15:.2f}" fill="#e5e7eb" font-size="13" text-anchor="middle" font-family="Arial">{_escape_xml(label_text)}</text>')
        else:
            import math
            dx, dy = x2 - x1, y2 - y1
            dist = max(1e-6, math.hypot(dx, dy))
            ux, uy = dx / dist, dy / dist
            sx, sy = x1 + ux * R, y1 + uy * R
            ex, ey = x2 - ux * R, y2 - uy * R
            nx, ny = -uy, ux
            curve_mag = (26 if (u, v) in bidir else 14)
            curve = curve_mag * (1 if u < v else -1)
            cx, cy = (sx + ex) / 2 + nx * curve, (sy + ey) / 2 + ny * curve
            svg.append(f'<path d="M {sx:.2f} {sy:.2f} Q {cx:.2f} {cy:.2f} {ex:.2f} {ey:.2f}" fill="none" stroke="{stroke_color}" stroke-width="2.6" marker-end="url(#{marker_id})" />')
            lx, ly = (sx + ex) / 2 + nx * (curve + 0), (sy + ey) / 2 + ny * (curve + 0)
            lw = max(30.0, len(label_text) * 7.5 + 14)
            svg.append(f'<rect x="{lx - lw/2:.2f}" y="{ly - 18:.2f}" width="{lw:.2f}" height="20" rx="7" ry="7" fill="#2d2d2d" stroke="#444" filter="url(#labelShadow)"/>')
            svg.append(f'<text x="{lx:.2f}" y="{ly - 4:.2f}" fill="#e5e7eb" font-size="13" text-anchor="middle" font-family="Arial">{_escape_xml(label_text)}</text>')

    for s, (x, y) in positions.items():
        is_accept = s in accept
        svg.append(f'<circle cx="{x}" cy="{y}" r="26" fill="#ffffff" stroke="{stroke_color}" stroke-width="2.6" filter="url(#nodeShadow)"/>')
        if is_accept:
            svg.append(f'<circle cx="{x}" cy="{y}" r="21" fill="none" stroke="{stroke_color}" stroke-width="2.6"/>')
        svg.append(f'<text x="{x}" y="{y+5}" fill="#111827" font-size="15" text-anchor="middle" font-family="Arial" font-weight="bold">{_escape_xml(str(s))}</text>')
        if s == start:
            svg.append(f'<line x1="{x-72}" y1="{y}" x2="{x-29}" y2="{y}" stroke="{stroke_color}" stroke-width="2.6" marker-end="url(#{marker_id})" />')

    svg.append('</svg>')
    return _data_url(''.join(svg))


def generate_comparison_svg(original: DFA, minimized: DFA) -> str:
    width, height = 1200, 700
    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg_parts.append('<rect x="0" y="0" width="100%" height="100%" fill="#1e1e1e"/>')
    svg_parts.append('<text x="200" y="40" fill="#e0e0e0" font-size="22" font-family="Arial" font-weight="bold">Original DFA</text>')
    svg_parts.append('<text x="800" y="40" fill="#e0e0e0" font-size="22" font-family="Arial" font-weight="bold">Minimized DFA</text>')

    def render_with_offset(dfa: DFA, dx: float, stroke_color: str, marker_id: str) -> str:
        positions = _layout_states(sorted(list(dfa.states)), 520, 560)
        positions = {k: (x + dx, y + 60) for k, (x, y) in positions.items()}
        start = dfa.start_state
        accept = set(dfa.accept_states)
        parts: List[str] = []
        parts.append(_arrow_marker_defs())
        edge_labels = _group_edge_labels(dfa.transitions)
        bidir = set()
        for (u, v) in list(edge_labels.keys()):
            if (v, u) in edge_labels and u != v:
                bidir.add((u, v)); bidir.add((v, u))
        R = 26.0
        for (u, v), labels in edge_labels.items():
            x1, y1 = positions[u]
            x2, y2 = positions[v]
            label_text = ','.join(sorted(set(labels)))
            if u == v:
                loop_r = 40
                parts.append(f'<path d="M {x1} {y1-loop_r} c -44 -42, 44 -42, 0 0" fill="none" stroke="{stroke_color}" stroke-width="2.6" marker-end="url(#{marker_id})"/>')
                lw = max(30.0, len(label_text) * 7.5 + 14)
                parts.append(f'<rect x="{x1 - lw/2:.2f}" y="{y1 - loop_r - 30:.2f}" width="{lw:.2f}" height="20" rx="7" ry="7" fill="#2d2d2d" stroke="#444" filter="url(#labelShadow)"/>')
                parts.append(f'<text x="{x1:.2f}" y="{y1 - loop_r - 15:.2f}" fill="#e5e7eb" font-size="13" text-anchor="middle" font-family="Arial">{_escape_xml(label_text)}</text>')
            else:
                import math
                dx_, dy_ = x2 - x1, y2 - y1
                dist = max(1e-6, math.hypot(dx_, dy_))
                ux, uy = dx_ / dist, dy_ / dist
                sx, sy = x1 + ux * R, y1 + uy * R
                ex, ey = x2 - ux * R, y2 - uy * R
                nx, ny = -uy, ux
                curve_mag = (26 if (u, v) in bidir else 14)
                curve = curve_mag * (1 if u < v else -1)
                cx_, cy_ = (sx + ex) / 2 + nx * curve, (sy + ey) / 2 + ny * curve
                parts.append(f'<path d="M {sx:.2f} {sy:.2f} Q {cx_:.2f} {cy_:.2f} {ex:.2f} {ey:.2f}" fill="none" stroke="{stroke_color}" stroke-width="2.6" marker-end="url(#{marker_id})" />')
                lx, ly = (sx + ex) / 2 + nx * (curve + 0), (sy + ey) / 2 + ny * (curve + 0)
                lw = max(30.0, len(label_text) * 7.5 + 14)
                parts.append(f'<rect x="{lx - lw/2:.2f}" y="{ly - 18:.2f}" width="{lw:.2f}" height="20" rx="7" ry="7" fill="#2d2d2d" stroke="#444" filter="url(#labelShadow)"/>')
                parts.append(f'<text x="{lx:.2f}" y="{ly - 4:.2f}" fill="#e5e7eb" font-size="13" text-anchor="middle" font-family="Arial">{_escape_xml(label_text)}</text>')
        for s, (x, y) in positions.items():
            parts.append(f'<circle cx="{x}" cy="{y}" r="26" fill="#ffffff" stroke="{stroke_color}" stroke-width="2.6" filter="url(#nodeShadow)"/>')
            if s in accept:
                parts.append(f'<circle cx="{x}" cy="{y}" r="21" fill="none" stroke="{stroke_color}" stroke-width="2.6"/>')
            parts.append(f'<text x="{x}" y="{y+5}" fill="#111827" font-size="15" text-anchor="middle" font-family="Arial" font-weight="bold">{_escape_xml(str(s))}</text>')
            if s == start:
                parts.append(f'<line x1="{x-72}" y1="{y}" x2="{x-29}" y2="{y}" stroke="{stroke_color}" stroke-width="2.6" marker-end="url(#{marker_id})" />')
        return ''.join(parts)

    svg_parts.append(_arrow_marker_defs())
    svg_parts.append(render_with_offset(original, 200, '#4a6fa5', 'arrow-blue'))
    svg_parts.append(render_with_offset(minimized, 700, '#10b981', 'arrow-green'))
    svg_parts.append('</svg>')
    return _data_url(''.join(svg_parts))


def generate_path_svg(dfa: DFA, input_string: str, trace: List[str]) -> str:
    width, height = 1000, 600
    positions = _layout_states(sorted(list(dfa.states)), width, height)
    start = dfa.start_state
    accept = set(dfa.accept_states)

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg.append(_arrow_marker_defs())
    svg.append('<rect x="0" y="0" width="100%" height="100%" fill="#1e1e1e"/>')

    path_edges = set()
    for i, sym in enumerate(input_string):
        u, v = trace[i], trace[i+1]
        path_edges.add((u, sym, v))

    # Build grouped labels for normal rendering
    edge_labels = _group_edge_labels(dfa.transitions)
    bidir = set()
    for (u, v) in list(edge_labels.keys()):
        if (v, u) in edge_labels and u != v:
            bidir.add((u, v)); bidir.add((v, u))

    R = 26.0
    for (u, v), labels in edge_labels.items():
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        label_text = ','.join(sorted(set(labels)))
        on_path = any((u, a, v) in path_edges for a in labels)
        color = '#ff0000' if on_path else '#4a6fa5'
        marker = 'url(#arrow-red)' if on_path else 'url(#arrow-blue)'
        if u == v:
            loop_r = 40
            svg.append(f'<path d="M {x1} {y1-loop_r} c -44 -42, 44 -42, 0 0" fill="none" stroke="{color}" stroke-width="2.6" marker-end="{marker}"/>')
            lw = max(30.0, len(label_text) * 7.5 + 14)
            svg.append(f'<rect x="{x1 - lw/2:.2f}" y="{y1 - loop_r - 30:.2f}" width="{lw:.2f}" height="20" rx="7" ry="7" fill="#2d2d2d" stroke="#444" filter="url(#labelShadow)"/>')
            svg.append(f'<text x="{x1:.2f}" y="{y1 - loop_r - 15:.2f}" fill="#e5e7eb" font-size="13" text-anchor="middle" font-family="Arial">{_escape_xml(label_text)}</text>')
        else:
            import math
            dx, dy = x2 - x1, y2 - y1
            dist = max(1e-6, math.hypot(dx, dy))
            ux, uy = dx / dist, dy / dist
            sx, sy = x1 + ux * R, y1 + uy * R
            ex, ey = x2 - ux * R, y2 - uy * R
            nx, ny = -uy, ux
            curve_mag = (26 if (u, v) in bidir else 14)
            curve = curve_mag * (1 if u < v else -1)
            cx, cy = (sx + ex) / 2 + nx * curve, (sy + ey) / 2 + ny * curve
            svg.append(f'<path d="M {sx:.2f} {sy:.2f} Q {cx:.2f} {cy:.2f} {ex:.2f} {ey:.2f}" fill="none" stroke="{color}" stroke-width="2.6" marker-end="{marker}" />')
            lx, ly = (sx + ex) / 2 + nx * (curve + 0), (sy + ey) / 2 + ny * (curve + 0)
            lw = max(30.0, len(label_text) * 7.5 + 14)
            svg.append(f'<rect x="{lx - lw/2:.2f}" y="{ly - 18:.2f}" width="{lw:.2f}" height="20" rx="7" ry="7" fill="#2d2d2d" stroke="#444" filter="url(#labelShadow)"/>')
            svg.append(f'<text x="{lx:.2f}" y="{ly - 4:.2f}" fill="#e5e7eb" font-size="13" text-anchor="middle" font-family="Arial">{_escape_xml(label_text)}</text>')

    for s, (x, y) in positions.items():
        is_accept = s in accept
        stroke = '#4a6fa5'
        svg.append(f'<circle cx="{x}" cy="{y}" r="26" fill="#ffffff" stroke="{stroke}" stroke-width="2.6" filter="url(#nodeShadow)"/>')
        if is_accept:
            svg.append(f'<circle cx="{x}" cy="{y}" r="21" fill="none" stroke="{stroke}" stroke-width="2.6"/>')
        svg.append(f'<text x="{x}" y="{y+5}" fill="#111827" font-size="15" text-anchor="middle" font-family="Arial" font-weight="bold">{_escape_xml(str(s))}</text>')
        if s == start:
            svg.append(f'<line x1="{x-72}" y1="{y}" x2="{x-29}" y2="{y}" stroke="#4a6fa5" stroke-width="2.6" marker-end="url(#arrow-blue)" />')

    svg.append('</svg>')
    return _data_url(''.join(svg))


def _nfa_transitions_to_json(transitions: Dict[Tuple[str, str], set]) -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = {}
    for (state, symbol), targets in transitions.items():
        if state not in out:
            out[state] = {}
        out[state][symbol] = sorted(list(targets))
    return out


class AppHandler(BaseHTTPRequestHandler):
    server_version = 'DFAMinimizer/1.0'

    def _send(self, code: int, body: bytes, content_type: str = 'text/plain; charset=utf-8') -> None:
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == '/' or path == '/index.html':
            file_path = TEMPLATES_DIR / 'index.html'
            if not file_path.exists():
                self._send(404, b'index not found')
                return
            content = file_path.read_bytes()
            self._send(200, content, CONTENT_TYPES['.html'])
            return
        if path.startswith('/static/'):
            file_path = ROOT / path.lstrip('/')
            if not file_path.exists() or not file_path.is_file():
                self._send(404, b'Not found')
                return
            ext = file_path.suffix.lower()
            ctype = CONTENT_TYPES.get(ext, 'application/octet-stream')
            self._send(200, file_path.read_bytes(), ctype)
            return
        self._send(404, b'Not found')

    def do_POST(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', '0'))
        body = self.rfile.read(length) if length > 0 else b''
        try:
            data = json.loads(body.decode('utf-8')) if body else {}
        except Exception:
            self._send(400, json.dumps({'success': False, 'error': 'Invalid JSON'}).encode('utf-8'), 'application/json')
            return

        if path == '/minimize':
            try:
                dfa = DFA.from_dict(data)
                minimized, table_filling_data = minimize_dfa_table_filling(dfa)
                original_image = generate_dfa_svg(dfa, 'Original DFA')
                minimized_image = generate_dfa_svg(minimized, 'Minimized DFA')
                comparison_image = generate_comparison_svg(dfa, minimized)
                res = {
                    'success': True,
                    'original_dfa': dfa.to_dict(),
                    'minimized_dfa': minimized.to_dict(),
                    'original_image': original_image,
                    'minimized_image': minimized_image,
                    'comparison_image': comparison_image,
                    'table_filling_data': table_filling_data,
                }
                self._send(200, json.dumps(res).encode('utf-8'), 'application/json')
            except Exception as e:
                self._send(200, json.dumps({'success': False, 'error': str(e)}).encode('utf-8'), 'application/json')
            return

        if path == '/convert_nfa':
            try:
                nfa = NFA.from_dict(data)
                dfa = nfa.to_dfa()
                nfa_image = generate_nfa_svg(nfa, 'Original NFA')
                dfa_image = generate_dfa_svg(dfa, 'Converted DFA')
                res = {
                    'success': True,
                    'nfa': {
                        'states': list(nfa.states),
                        'alphabet': list(nfa.alphabet),
                        'transitions': _nfa_transitions_to_json(nfa.transitions),
                        'start_state': nfa.start_state,
                        'accept_states': list(nfa.accept_states),
                    },
                    'dfa': dfa.to_dict(),
                    'nfa_image': nfa_image,
                    'dfa_image': dfa_image,
                }
                self._send(200, json.dumps(res).encode('utf-8'), 'application/json')
            except Exception as e:
                self._send(200, json.dumps({'success': False, 'error': str(e)}).encode('utf-8'), 'application/json')
            return

        if path == '/dfa_to_regex':
            try:
                payload = data['dfa'] if 'dfa' in data else data
                dfa = DFA.from_dict(payload)
                result = dfa_to_regex_arden(dfa)
                self._send(200, json.dumps({'success': True, **result}).encode('utf-8'), 'application/json')
            except Exception as e:
                self._send(200, json.dumps({'success': False, 'error': str(e)}).encode('utf-8'), 'application/json')
            return

        if path == '/test_string':
            try:
                dfa_data = data.get('dfa')
                input_string = data.get('input_string', '')
                if not dfa_data or input_string is None:
                    self._send(200, json.dumps({'success': False, 'error': 'Missing DFA or input string'}).encode('utf-8'), 'application/json')
                    return
                dfa = DFA.from_dict(dfa_data)
                result = dfa.process_string_with_trace(input_string)
                path_image = generate_path_svg(dfa, input_string, result['trace'])
                out = {
                    'success': True,
                    'trace': result['trace'],
                    'accepted': result['accepted'],
                    'path_image': path_image,
                }
                self._send(200, json.dumps(out).encode('utf-8'), 'application/json')
            except Exception as e:
                self._send(200, json.dumps({'success': False, 'error': str(e)}).encode('utf-8'), 'application/json')
            return

        self._send(404, b'Not found')


def run_server():
    port = int(os.environ.get('PORT', '5000'))
    addr = ('0.0.0.0', port)
    httpd = HTTPServer(addr, AppHandler)
    print(f'Serving on http://{addr[0]}:{addr[1]}')
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
