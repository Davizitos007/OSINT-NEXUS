"""
OSINT-Nexus Graph View Tab
Interactive force-directed graph visualization with Maltego-style aesthetics.
"""

import math
import random
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem,
    QGraphicsPathItem, QGraphicsDropShadowEffect, QFrame,
    QLabel, QPushButton, QSlider, QSplitter, QScrollArea,
    QGroupBox, QFormLayout, QToolBar, QToolButton, QSizePolicy,
    QGroupBox, QFormLayout, QToolBar, QToolButton, QSizePolicy,
    QGraphicsItem, QGraphicsRectItem, QMenu, QApplication, QComboBox,
    QFileDialog, QInputDialog, QTextEdit
)
from PyQt6.QtCore import (
    Qt, QPointF, QRectF, QTimer, pyqtSignal, QLineF, QPropertyAnimation,
    QEasingCurve, QObject, pyqtProperty
)
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath,
    QRadialGradient, QLinearGradient, QTransform, QPolygonF
)

from .styles import COLORS, get_entity_color
from .styles import COLORS, get_entity_color
from .graph_layouts import GraphLayouts


class InteractiveGraphView(QGraphicsView):
    """Custom GraphicsView handling zoom and pan interactions."""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setInteractive(True)
        
        # Pan state
        self._is_panning = False
        self._last_pan_pos = QPointF()

    def wheelEvent(self, event):
        """Handle zoom on wheel."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom
            factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale(factor, factor)
            else:
                self.scale(1 / factor, 1 / factor)
            event.accept()
        else:
            # Default scroll or Zoom without ctrl if preferred?
            # User wants zoom on scroll usually in graph apps
            factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale(factor, factor)
            else:
                self.scale(1 / factor, 1 / factor)
            event.accept()

    def mousePressEvent(self, event):
        """Handle middle click for panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle panning drag."""
        if self._is_panning:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """End panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)



@dataclass
class NodeData:
    """Data associated with a graph node."""
    id: int
    entity_type: str
    value: str
    label: str
    attributes: Dict[str, Any]
    x: float = 0
    y: float = 0
    vx: float = 0  # velocity x
    vy: float = 0  # velocity y
    pinned: bool = False


@dataclass
class EdgeData:
    """Data associated with a graph edge."""
    source_id: int
    target_id: int
    relationship: str
    weight: float = 1.0


class GraphNode(QGraphicsEllipseItem):
    """Interactive graph node with visual styling."""
    
    NODE_RADIUS = 32
    ICON_SIZE = 20
    
    # Unicode icons for entity types
    ENTITY_ICONS = {
        "email": "✉",
        "domain": "🌐",
        "ip": "📡",
        "phone": "📱",
        "username": "👤",
        "person": "👤",
        "company": "🏢",
        "subdomain": "🔗",
        "hostname": "💻",
        "document": "📄",
        "location": "📍",
        "network": "🌐",
        "url": "🔗",
        "port": "🔌",
        "vulnerability": "⚠",
        "hash": "🔐",
        "file": "📁",
        "certificate": "📜",
        "asn": "🏛",
        "netblock": "📦",
        "service": "⚙",
        "technology": "🔧",
        "social": "💬",
    }
    
    def __init__(self, node_data: NodeData, parent=None):
        size = self.NODE_RADIUS * 2
        super().__init__(-self.NODE_RADIUS, -self.NODE_RADIUS, size, size, parent)
        
        self.node_data = node_data
        self.setPos(node_data.x, node_data.y)
        
        # Enable interactions
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._is_hovered = False
        self._connected_edges: List['GraphEdge'] = []
        
        # Set up visual appearance
        self._setup_appearance()
    
    def _setup_appearance(self):
        """Configure node visual appearance."""
        color = get_entity_color(self.node_data.entity_type)
        
        # Create gradient brush
        gradient = QRadialGradient(0, -self.NODE_RADIUS / 3, self.NODE_RADIUS * 1.5)
        gradient.setColorAt(0, QColor(color).lighter(150))
        gradient.setColorAt(0.5, QColor(color))
        gradient.setColorAt(1, QColor(color).darker(120))
        
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor(color).darker(140), 2))
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(3, 3)
        self.setGraphicsEffect(shadow)
        
        # Add icon
        # Check for specific platform attribute first
        icon = None
        platform = self.node_data.attributes.get("platform", "").lower()
        
        PLATFORM_ICONS = {
            "facebook": "📘",
            "twitter": "🐦",
            "x": "𝕏",
            "instagram": "📸",
            "linkedin": "💼",
            "github": "🐙",
            "steam": "🎮",
            "whatsapp": "📞",
            "google": "🔍",
            "youtube": "📺",
            "reddit": "🤖",
            "telegram": "✈️",
            "tiktok": "🎵",
            "pinterest": "📌",
        }
        
        # Try finding icon by platform key
        for p_key, p_icon in PLATFORM_ICONS.items():
            if p_key in platform:
                icon = p_icon
                break
        
        # Fallback to Entity Type icon
        if not icon:
            icon = self.ENTITY_ICONS.get(self.node_data.entity_type, "⚡")
            
        self.icon_text = QGraphicsTextItem(icon, self)
        self.icon_text.setDefaultTextColor(QColor("#ffffff"))
        font = QFont("Segoe UI Emoji", 14)
        self.icon_text.setFont(font)
        
        # Center the icon
        icon_rect = self.icon_text.boundingRect()
        self.icon_text.setPos(-icon_rect.width() / 2, -icon_rect.height() / 2)
        
        # Add label below node
        self.label_text = QGraphicsTextItem(self._truncate_label(self.node_data.label), self)
        self.label_text.setDefaultTextColor(QColor(COLORS["text_primary"]))
        label_font = QFont("Segoe UI", 9)
        self.label_text.setFont(label_font)
        
        # Center the label below node
        label_rect = self.label_text.boundingRect()
        self.label_text.setPos(-label_rect.width() / 2, self.NODE_RADIUS + 5)
    
    def _truncate_label(self, label: str, max_length: int = 20) -> str:
        """Truncate long labels."""
        if len(label) > max_length:
            return label[:max_length-3] + "..."
        return label
    
    def add_edge(self, edge: 'GraphEdge'):
        """Register a connected edge."""
        self._connected_edges.append(edge)
    
    def update_edges(self):
        """Update all connected edges."""
        for edge in self._connected_edges:
            edge.update_position()
    
    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update node data
            self.node_data.x = self.pos().x()
            self.node_data.y = self.pos().y()
            # Update connected edges
            self.update_edges()
        return super().itemChange(change, value)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter."""
        self._is_hovered = True
        self.setScale(1.15)
        
        # Highlight connected edges
        for edge in self._connected_edges:
            edge.set_highlighted(True)
        
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave."""
        self._is_hovered = False
        self.setScale(1.0)
        
        # Un-highlight connected edges
        for edge in self._connected_edges:
            edge.set_highlighted(False)
        
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.node_data.pinned = True
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.node_data.pinned = False
        super().mouseReleaseEvent(event)


class GraphEdge(QGraphicsPathItem):
    """Visual edge connecting two nodes."""
    
    def __init__(self, source: GraphNode, target: GraphNode, 
                 edge_data: EdgeData, parent=None):
        super().__init__(parent)
        
        self.source = source
        self.target = target
        self.edge_data = edge_data
        self._is_highlighted = False
        
        # Register with nodes
        source.add_edge(self)
        target.add_edge(self)
        
        # Set up appearance
        self._setup_appearance()
        self.update_position()
    
    def _setup_appearance(self):
        """Configure edge appearance."""
        # Scale width based on weight, clamped between 1 and 8
        width = max(1, min(8, self.edge_data.weight * 2))
        
        self._normal_pen = QPen(QColor(COLORS["border_default"]), width)
        self._normal_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        self._highlighted_pen = QPen(QColor(COLORS["accent_primary"]), width + 2)
        self._highlighted_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        self.setPen(self._normal_pen)
        self.setZValue(-1)  # Draw behind nodes
        
        # Create label
        if self.edge_data.relationship:
            self.label = QGraphicsTextItem(self.edge_data.relationship, self)
            self.label.setDefaultTextColor(QColor(COLORS["text_muted"]))
            font = QFont("Segoe UI", 8)
            self.label.setFont(font)
        else:
            self.label = None
    
    def set_highlighted(self, highlighted: bool):
        """Set edge highlight state."""
        self._is_highlighted = highlighted
        self.setPen(self._highlighted_pen if highlighted else self._normal_pen)
        
        if self.label:
            self.label.setDefaultTextColor(
                QColor(COLORS["accent_primary"] if highlighted else COLORS["text_muted"])
            )
    
    def update_position(self):
        """Update edge position based on node positions."""
        source_pos = self.source.pos()
        target_pos = self.target.pos()
        
        # Calculate direction
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        # Normalize
        dx /= length
        dy /= length
        
        # Calculate edge endpoints (at node boundaries)
        r = GraphNode.NODE_RADIUS + 2
        start = QPointF(
            source_pos.x() + dx * r,
            source_pos.y() + dy * r
        )
        end = QPointF(
            target_pos.x() - dx * r,
            target_pos.y() - dy * r
        )
        
        # Create curved path
        path = QPainterPath()
        path.moveTo(start)
        
        # Add slight curve for visual appeal
        mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
        offset = 20  # Curve offset
        
        # Perpendicular offset
        perp_x = -dy * offset
        perp_y = dx * offset
        
        control = QPointF(mid.x() + perp_x, mid.y() + perp_y)
        path.quadTo(control, end)
        
        self.setPath(path)
        
        # Add arrowhead
        self._draw_arrowhead(end, dx, dy)
        
        # Position label at midpoint
        if self.label:
            label_rect = self.label.boundingRect()
            self.label.setPos(
                mid.x() + perp_x - label_rect.width() / 2,
                mid.y() + perp_y - label_rect.height() / 2
            )
    
    def _draw_arrowhead(self, tip: QPointF, dx: float, dy: float):
        """Draw arrowhead at edge end."""
        arrow_size = 10
        angle = math.atan2(dy, dx)
        
        # Arrowhead points
        p1 = QPointF(
            tip.x() - arrow_size * math.cos(angle - math.pi / 6),
            tip.y() - arrow_size * math.sin(angle - math.pi / 6)
        )
        p2 = QPointF(
            tip.x() - arrow_size * math.cos(angle + math.pi / 6),
            tip.y() - arrow_size * math.sin(angle + math.pi / 6)
        )
        
        path = self.path()
        path.moveTo(tip)
        path.lineTo(p1)
        path.moveTo(tip)
        path.lineTo(p2)
        self.setPath(path)


class ForceDirectedLayout:
    """Force-directed graph layout algorithm."""
    
    def __init__(self, nodes: Dict[int, NodeData], edges: List[EdgeData]):
        self.nodes = nodes
        self.edges = edges
        
        # Physics parameters
        self.repulsion = 8000  # Node repulsion strength
        self.attraction = 0.05  # Edge attraction strength
        self.damping = 0.85  # Velocity damping
        self.min_velocity = 0.1
        self.max_velocity = 50
    
    def step(self) -> bool:
        """
        Perform one simulation step.
        Returns True if layout has stabilized.
        """
        if not self.nodes:
            return True
        
        # Calculate forces
        forces: Dict[int, Tuple[float, float]] = {}
        
        for node_id in self.nodes:
            forces[node_id] = (0.0, 0.0)
        
        node_list = list(self.nodes.values())
        
        # Repulsion forces between all nodes
        for i, node1 in enumerate(node_list):
            for node2 in node_list[i + 1:]:
                dx = node2.x - node1.x
                dy = node2.y - node1.y
                dist_sq = dx * dx + dy * dy
                
                if dist_sq < 1:
                    dist_sq = 1
                
                dist = math.sqrt(dist_sq)
                force = self.repulsion / dist_sq
                
                fx = (dx / dist) * force
                fy = (dy / dist) * force
                
                f1 = forces[node1.id]
                f2 = forces[node2.id]
                forces[node1.id] = (f1[0] - fx, f1[1] - fy)
                forces[node2.id] = (f2[0] + fx, f2[1] + fy)
        
        # Attraction forces along edges
        for edge in self.edges:
            if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
                continue
            
            source = self.nodes[edge.source_id]
            target = self.nodes[edge.target_id]
            
            dx = target.x - source.x
            dy = target.y - source.y
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist < 1:
                continue
            
            force = dist * self.attraction * edge.weight
            fx = (dx / dist) * force
            fy = (dy / dist) * force
            
            fs = forces[source.id]
            ft = forces[target.id]
            forces[source.id] = (fs[0] + fx, fs[1] + fy)
            forces[target.id] = (ft[0] - fx, ft[1] - fy)
        
        # Center gravity (weak pull toward center)
        for node in node_list:
            fx, fy = forces[node.id]
            fx -= node.x * 0.001
            fy -= node.y * 0.001
            forces[node.id] = (fx, fy)
        
        # Apply forces
        stable = True
        for node in node_list:
            if node.pinned:
                node.vx = 0
                node.vy = 0
                continue
            
            fx, fy = forces[node.id]
            
            # Update velocity
            node.vx = (node.vx + fx) * self.damping
            node.vy = (node.vy + fy) * self.damping
            
            # Clamp velocity
            speed = math.sqrt(node.vx * node.vx + node.vy * node.vy)
            if speed > self.max_velocity:
                scale = self.max_velocity / speed
                node.vx *= scale
                node.vy *= scale
            
            elif speed > self.min_velocity:
                stable = False
            
            # Update position
            node.x += node.vx
            node.y += node.vy
        
        return stable


class GraphViewTab(QWidget):
    """
    Interactive graph visualization tab.
    Displays OSINT entities and their relationships in a force-directed layout.
        """
    
    # Signal emitted when a node is selected
    node_selected = pyqtSignal(object)  # NodeData
    # Signal emitted when a transform is requested
    transform_requested = pyqtSignal(object, str)  # NodeData, transform_name
    machine_requested = pyqtSignal(object, str)    # node_data, machine_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.machine_manager = None
        
        
        # Pan state
        self._is_panning = False
        self._last_pan_pos = QPointF()
        
        # Linking state
        self._linking_source = None
        
        self._nodes: Dict[int, NodeData] = {}
        self._edges: List[EdgeData] = []
        self._node_items: Dict[int, GraphNode] = {}
        self._edge_items: List[GraphEdge] = []
        
        self._layout_engine: Optional[ForceDirectedLayout] = None
        self._layout_timer = QTimer()
        self._layout_timer.timeout.connect(self._layout_step)
        
        self._setup_ui()
        
        # Enable context menu
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._show_context_menu)
    
    def set_machine_manager(self, manager):
        """Set the machine manager instance."""
        self.machine_manager = manager
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for graph and inspector
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === Left: Graph View ===
        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(0)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {COLORS['background_medium']};
                border-bottom: 1px solid {COLORS['border_default']};
                padding: 4px;
            }}
        """)
        
        # Zoom controls
        zoom_in_btn = QToolButton()
        zoom_in_btn.setText("🔍+")
        zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar.addWidget(zoom_in_btn)
        
        zoom_out_btn = QToolButton()
        zoom_out_btn.setText("🔍-")
        zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar.addWidget(zoom_out_btn)
        
        fit_btn = QToolButton()
        fit_btn.setText("⬜ Fit")
        fit_btn.clicked.connect(self._fit_to_view)
        toolbar.addWidget(fit_btn)
        
        # Pan toggle
        self.pan_btn = QToolButton()
        self.pan_btn.setText("✋ Pan")
        self.pan_btn.setCheckable(True)
        self.pan_btn.clicked.connect(self._toggle_drag_mode)
        toolbar.addWidget(self.pan_btn)
        
        toolbar.addSeparator()
        
        # Layout controls
        layout_btn = QToolButton()
        layout_btn.setText("🔄 Relayout")
        layout_btn.clicked.connect(self._restart_layout)
        toolbar.addWidget(layout_btn)
        
        clear_btn = QToolButton()
        clear_btn.setText("🗑 Clear")
        clear_btn.clicked.connect(self.clear_graph)
        toolbar.addWidget(clear_btn)
        
        # Layout control
        self.layout_selector = QComboBox()
        self.layout_selector.addItems(["Force Directed", "Circle", "Grid", "Radial"])
        self.layout_selector.currentTextChanged.connect(self._change_layout)
        self.layout_selector.setFixedWidth(120)
        toolbar.addWidget(QLabel("Layout: "))
        toolbar.addWidget(self.layout_selector)
        
        toolbar.addSeparator()
        
        # Stats
        self.stats_label = QLabel("Nodes: 0 | Edges: 0")
        self.stats_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 0 10px;")
        toolbar.addWidget(self.stats_label)
        
        graph_layout.addWidget(toolbar)
        
        # Graphics view
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor(COLORS["background_dark"])))
        
        self.view = InteractiveGraphView(self.scene)
        
        # Add grid pattern
        self._add_grid()
        
        graph_layout.addWidget(self.view)
        
        splitter.addWidget(graph_container)
        
        # === Right: Node Inspector ===
        inspector = self._create_inspector()
        splitter.addWidget(inspector)
        
        splitter.setSizes([800, 300])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Connect scene selection
        self.scene.selectionChanged.connect(self._on_selection_changed)
    
    def _add_grid(self):
        """Add a subtle grid pattern to the background."""
        grid_size = 50
        grid_color = QColor(COLORS["border_muted"])
        grid_pen = QPen(grid_color, 0.5)
        
        # We'll draw grid lines when needed
        # For now, set a larger scene rect
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
    
    def _create_inspector(self) -> QWidget:
        """Create the node inspector panel."""
        inspector = QFrame()
        inspector.setObjectName("cardFrame")
        inspector.setMinimumWidth(280)
        inspector.setMaximumWidth(400)
        
        layout = QVBoxLayout(inspector)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("🔍 Node Inspector")
        header.setObjectName("headingLabel")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Node info
        self.inspector_type = QLabel("No node selected")
        self.inspector_type.setWordWrap(True)
        self.inspector_type.setObjectName("subheadingLabel")
        layout.addWidget(self.inspector_type)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border_default']};")
        layout.addWidget(sep)
        
        # Attributes scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.attributes_container = QWidget()
        self.attributes_layout = QFormLayout(self.attributes_container)
        self.attributes_layout.setSpacing(8)
        scroll.setWidget(self.attributes_container)
        
        layout.addWidget(scroll, 1)
        
        layout.addWidget(scroll, 1)
        
        # === Activity Log ===
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(4, 4, 4, 4)
        
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(150)
        self.log_widget.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background_dark']};
                border: 1px solid {COLORS['border_default']};
                border-radius: 4px;
                color: {COLORS['text_primary']};
                font-family: Consolas, monospace;
                font-size: 11px;
            }}
        """)
        log_layout.addWidget(self.log_widget)
        layout.addWidget(log_group)

        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        expand_btn = QPushButton("🔗 Expand Node")
        expand_btn.clicked.connect(self._expand_selected_node)
        actions_layout.addWidget(expand_btn)
        
        delete_btn = QPushButton("🗑 Delete Node")
        delete_btn.setProperty("danger", True)
        delete_btn.clicked.connect(self._delete_selected_node)
        actions_layout.addWidget(delete_btn)
        
        # Store refs to enable/disable
        self.btn_expand = expand_btn
        self.btn_delete = delete_btn
        
        return inspector
        
    def log_message(self, message: str, level: str = "info"):
        """Log a message to the activity log."""
        if not hasattr(self, 'log_widget'):
            return
            
        color = COLORS["text_primary"]
        if level == "error": color = COLORS.get("accent_danger", "red")
        elif level == "success": color = COLORS.get("accent_success", "green")
        elif level == "warning": color = COLORS.get("accent_warning", "orange")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = f'<div style="color: {color}">[{timestamp}] {message}</div>'
        self.log_widget.append(html)
        
        # Scroll to bottom
        sb = self.log_widget.verticalScrollBar()
        sb.setValue(sb.maximum())
    
    # === Private Methods ===
    
    def _expand_selected_node(self):
        
        layout.addWidget(actions_group)
        
        return inspector
    
    def _zoom_in(self):
        """Zoom in the graph view."""
        self.view.scale(1.2, 1.2)
    
    def _zoom_out(self):
        """Zoom out the graph view."""
        self.view.scale(0.8, 0.8)
    
    def _fit_to_view(self):
        """Fit all nodes in the view."""
        if self._node_items:
            rect = self.scene.itemsBoundingRect()
            rect.adjust(-100, -100, 100, 100)
            self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def _toggle_drag_mode(self, checked):
        """Toggle between pan and select modes."""
        if checked:
            self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.view.setCursor(Qt.CursorShape.OpenHandCursor)
            self.pan_btn.setText("🖱️ Select")
        else:
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.view.setCursor(Qt.CursorShape.ArrowCursor)
            self.pan_btn.setText("✋ Pan")
    
    def _restart_layout(self):
        """Restart the force-directed layout."""
        if self._nodes:
            # Randomize positions
            for node in self._nodes.values():
                node.x = random.uniform(-300, 300)
                node.y = random.uniform(-300, 300)
                node.vx = 0
                node.vy = 0
            
            # Update node positions
            for node_id, item in self._node_items.items():
                node = self._nodes[node_id]
                item.setPos(node.x, node.y)
            
            
            self._change_layout("Force Directed")
    
    def _change_layout(self, layout_name: str):
        """Switch graph layout."""
        if layout_name == "Force Directed":
            self._layout_engine = ForceDirectedLayout(self._nodes, self._edges)
            self._layout_timer.start(16)
        else:
            self._layout_timer.stop()
            self._layout_engine = None  # Disable physics
            self._apply_static_layout(layout_name)
    
    def _apply_static_layout(self, layout_name: str):
        """Apply a static layout algorithm."""
        node_ids = list(self._nodes.keys())
        if not node_ids:
            return
            
        positions = {}
        
        if layout_name == "Circle":
            positions = GraphLayouts.circle_layout(node_ids)
        elif layout_name == "Grid":
            positions = GraphLayouts.grid_layout(node_ids)
        elif layout_name == "Radial":
            # Use selected node as root, or first node
            root_id = node_ids[0]
            selected = self.scene.selectedItems()
            if selected and isinstance(selected[0], GraphNode):
                root_id = selected[0].node_data.id
                
            edges_list = [(e.source_id, e.target_id) for e in self._edges]
            positions = GraphLayouts.radial_layout(node_ids, root_id, edges_list)
            
        # Animate to new positions
        for node_id, (x, y) in positions.items():
            if node_id in self._node_items:
                item = self._node_items[node_id]
                node_data = self._nodes[node_id]
                
                # Update data
                node_data.x = x
                node_data.y = y
                
                # Simple animation or setPos
                item.setPos(x, y)
                
        # Force redraw edges
        for edge_item in self._edge_items:
            edge_item.update_position()
            
        self.view.centerOn(0, 0)


    
    def _layout_step(self):
        """Perform one layout step."""
        if not self._layout_engine:
            self._layout_timer.stop()
            return
        
        stable = self._layout_engine.step()
        
        # Update node positions
        for node_id, item in self._node_items.items():
            if node_id in self._nodes:
                node = self._nodes[node_id]
                item.setPos(node.x, node.y)
        
        if stable:
            self._layout_timer.stop()
    
    def _on_selection_changed(self):
        """Handle node selection change."""
        try:
            selected = self.scene.selectedItems()
            
            if selected and isinstance(selected[0], GraphNode):
                node_item = selected[0]
                
                # Handle Linking Mode
                if self._linking_source:
                    if node_item != self._linking_source:
                        self._finish_connection(node_item)
                    return
                
                self._update_inspector(node_item.node_data)
                self.node_selected.emit(node_item.node_data)
            else:
                self._clear_inspector()
                # If background selected, maybe cancel linking?
                if self._linking_source:
                    self._cancel_connection_mode()

        except Exception as e:
            print(f"Selection error: {e}")
        except RuntimeError:
            # Scene was deleted (window closing)
            pass
    
    def _update_inspector(self, node_data: NodeData):
        """Update the inspector panel with node data."""
        icon = GraphNode.ENTITY_ICONS.get(node_data.entity_type, "⚡")
        self.inspector_type.setText(f"{icon} {node_data.entity_type.title()}")
        
        # Clear existing attributes
        while self.attributes_layout.count():
            item = self.attributes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add value
        value_label = QLabel(node_data.value)
        value_label.setWordWrap(True)
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.attributes_layout.addRow("Value:", value_label)
        
        # Add label if different
        if node_data.label != node_data.value:
            label_label = QLabel(node_data.label)
            label_label.setWordWrap(True)
            self.attributes_layout.addRow("Label:", label_label)
        
        # Add attributes
        for key, value in node_data.attributes.items():
            if key in ("source",):
                continue
            
            attr_value = QLabel(str(value) if not isinstance(value, (list, dict)) else str(value)[:100])
            attr_value.setWordWrap(True)
            attr_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            attr_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.attributes_layout.addRow(f"{key.title()}:", attr_value)

        # Enable actions
        if hasattr(self, 'btn_expand'):
            try:
                self.btn_expand.setEnabled(True)
            except RuntimeError: pass
            
        if hasattr(self, 'btn_delete'):
            try:
                self.btn_delete.setEnabled(True)
            except RuntimeError: pass
    
    def _clear_inspector(self):
        """Clear the inspector panel."""
        self.inspector_type.setText("No node selected")
        
        while self.attributes_layout.count():
            item = self.attributes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Disable actions
        try:
            if hasattr(self, 'btn_expand') and self.btn_expand:
                self.btn_expand.setEnabled(False)
            if hasattr(self, 'btn_delete') and self.btn_delete:
                self.btn_delete.setEnabled(False)
        except RuntimeError:
            # Widget already deleted
            pass
        except Exception:
            pass
        except RuntimeError:
            pass # Widget already deleted
    
    def _update_stats(self):
        """Update the stats label."""
        self.stats_label.setText(f"Nodes: {len(self._nodes)} | Edges: {len(self._edges)}")
    
    # === Public API ===
    
    def add_node(self, entity_id: int, entity_type: str, value: str,
                 label: str, attributes: Dict[str, Any] = None) -> int:
        """Add a node to the graph."""
        if entity_id in self._nodes:
            return entity_id
        
        # Random initial position near center
        scale = 100
        x = (random.random() - 0.5) * scale
        y = (random.random() - 0.5) * scale
        
        node_data = NodeData(
            id=entity_id,
            entity_type=entity_type,
            value=value,
            label=label,
            attributes=attributes or {},
            x=x, y=y
        )
        self._nodes[entity_id] = node_data
        
        # Create visual node
        node_item = GraphNode(node_data)
        self.scene.addItem(node_item)
        self._node_items[entity_id] = node_item
        
        self._update_stats()
        
        # Trigger layout to organize new node
        if self._layout_engine:
            if not self._layout_timer.isActive():
                 self._layout_timer.start(16)
        else:
             self._change_layout("Force Directed")
             
        return entity_id
    
    def add_connection(self, source_entity: Any, target_entity: Any, relationship: str):
        """Add a connection (edge) between two entities."""
        source_id = source_entity.id
        target_id = target_entity.id
        
        # Ensure nodes exist
        if source_id not in self._nodes:
            self.add_entity(source_entity)
        if target_id not in self._nodes:
            self.add_entity(target_entity)
            
        # Check if edge already exists
        for edge in self._edges:
            if (edge.source_id == source_id and edge.target_id == target_id and 
                edge.relationship == relationship):
                # Increase weight
                edge.weight += 0.5
                # Update visual
                self._update_edge_visual(edge)
                return
        
        # Create new edge
        edge_data = EdgeData(source_id, target_id, relationship)
        self._edges.append(edge_data)
        
        source_node = self._node_items[source_id]
        target_node = self._node_items[target_id]
        
        edge_item = GraphEdge(source_node, target_node, edge_data)
        self.scene.addItem(edge_item)
        self._edge_items.append(edge_item)
        
        self._update_stats()
        self._update_hub_sizes()
    
    def _update_edge_visual(self, edge_data: EdgeData):
        """Update visual style of an edge after data change."""
        for item in self._edge_items:
            if item.edge_data == edge_data:
                # Re-run setup appearance
                item._setup_appearance()
                item.setPen(item._normal_pen)
                break
                
    def _update_hub_sizes(self):
        """Update node sizes based on degree (hub detection)."""
        # Calculate degrees
        degrees = {}
        for edge in self._edges:
            degrees[edge.source_id] = degrees.get(edge.source_id, 0) + 1
            degrees[edge.target_id] = degrees.get(edge.target_id, 0) + 1
            
        # Update scales
        for node_id, item in self._node_items.items():
            degree = degrees.get(node_id, 0)
            # Scale factor: 1.0 (base) + 0.1 per connection, max 2.5
            scale = min(2.5, 1.0 + (degree * 0.1))
            
            # Use property animation for smooth sizing if desired, 
            # but direct scale is fine for now
            item.setTransform(QTransform().scale(scale, scale))
    
    def add_entity(self, entity):
        """Add an entity from the database model."""
        self.add_node(
            entity_id=entity.id,
            entity_type=entity.entity_type,
            value=entity.value,
            label=entity.label,
            attributes=entity.attributes
        )
    

    
    def start_layout_animation(self):
        """Start the force-directed layout animation."""
        if hasattr(self, 'layout_selector'):
            self._change_layout(self.layout_selector.currentText())
        else:
            self._change_layout("Force Directed")
    
    def clear_graph(self):
        """Clear all nodes and edges."""
        self._layout_timer.stop()
        self._layout_engine = None
        
        for item in self._edge_items:
            self.scene.removeItem(item)
        for item in self._node_items.values():
            self.scene.removeItem(item)
        
        self._nodes.clear()
        self._edges.clear()
        self._node_items.clear()
        self._edge_items.clear()
        
        self._clear_inspector()
        self._update_stats()
    

    def _delete_selected_node(self):
        """Delete all currently selected nodes."""
        try:
            selected_items = self.scene.selectedItems()
            if not selected_items:
                return
                
            # Resolve to GraphNodes (checking parents if a label/icon was selected)
            nodes_to_delete_ids = set()
            for item in selected_items:
                # Walk up to find GraphNode
                current = item
                while current:
                    if isinstance(current, GraphNode):
                        nodes_to_delete_ids.add(current.node_data.id)
                        break
                    current = current.parentItem()
            
            if not nodes_to_delete_ids:
                return

            self.log_message(f"Deleting {len(nodes_to_delete_ids)} node(s)...", "info")

            # 1. Collect all edges to remove
            edges_to_remove = []
            for edge in self._edges:
                if edge.source_id in nodes_to_delete_ids or edge.target_id in nodes_to_delete_ids:
                    edges_to_remove.append(edge)
                    
            # 2. Remove edge items from scene
            edge_items_to_remove = []
            for edge_item in self._edge_items:
                if edge_item.edge_data in edges_to_remove:
                    edge_items_to_remove.append(edge_item)
                    self.scene.removeItem(edge_item)
            
            for item in edge_items_to_remove:
                if item in self._edge_items:
                    self._edge_items.remove(item)
                    
            # 3. Remove edges from data
            for edge in edges_to_remove:
                if edge in self._edges:
                    self._edges.remove(edge)

            # 4. Remove node items and data
            for node_id in nodes_to_delete_ids:
                if node_id in self._node_items:
                    item = self._node_items.pop(node_id)
                    self.scene.removeItem(item)
                
                if node_id in self._nodes:
                    del self._nodes[node_id]

            self._clear_inspector()
            self._update_stats()
            
        except Exception as e:
            self.log_message(f"Delete Failed: {e}", "error")

        self._clear_inspector()
        self._update_stats()

    def _start_connection_mode(self, source_item):
        """Start manual connection mode."""
        self._linking_source = source_item
        self.view.setCursor(Qt.CursorShape.CrossCursor)
        # Visual feedback could be added here
    
    def _cancel_connection_mode(self):
        """Cancel linking."""
        self._linking_source = None
        self.view.setCursor(Qt.CursorShape.ArrowCursor)

    def _finish_connection(self, target_item):
        """Complete the connection."""
        source = self._linking_source
        self._cancel_connection_mode()
        
        if source == target_item:
            return

        # Ask for relationship
        rel, ok = QInputDialog.getText(self, "Link Nodes", "Relationship Label:", text="related_to")
        if ok:
            # Create dummy entities wrapping data to satisfy add_connection signature
            from ..database import Entity
            s_ent = Entity(id=source.node_data.id, entity_type=source.node_data.entity_type, value=source.node_data.value)
            t_ent = Entity(id=target_item.node_data.id, entity_type=target_item.node_data.entity_type, value=target_item.node_data.value)
            
            self.add_connection(s_ent, t_ent, rel or "related_to")
            
    def _add_manual_entity(self, pos):
        """Add a new entity manually."""
        types = ["person", "company", "domain", "ip", "email", "username", "phone", "url", "location"]
        type_str, ok = QInputDialog.getItem(self, "Add Entity", "Type:", types, 0, False)
        if not ok: return
        
        value, ok = QInputDialog.getText(self, "Add Entity", "Value:")
        if not ok or not value: return
        
        import random
        new_id = random.randint(1000000, 9999999) 
        
        from ..database import Entity
        entity = Entity(
            id=new_id, 
            entity_type=type_str, 
            value=value, 
            label=value,
            attributes={"source": "manual"}
        )
        self.add_entity(entity)
        
        # Position
        if new_id in self._node_items:
            scene_pos = self.view.mapToScene(pos)
            self._node_items[new_id].setPos(scene_pos)
            self._nodes[new_id].x = scene_pos.x()
            self._nodes[new_id].y = scene_pos.y()

    def _rename_edge(self, edge_item):
        """Rename a relationship."""
        current_rel = edge_item.edge_data.relationship
        new_rel, ok = QInputDialog.getText(self, "Rename Edge", "Relationship:", text=current_rel)
        if ok and new_rel:
            edge_item.edge_data.relationship = new_rel
            if edge_item.label:
                edge_item.label.setPlainText(new_rel)
                
    def _delete_edge(self, edge_item):
        """Delete a specific edge."""
        if edge_item.edge_data in self._edges:
            self._edges.remove(edge_item.edge_data)
        if edge_item in self._edge_items:
            self.scene.removeItem(edge_item)
            self._edge_items.remove(edge_item)
        self._update_stats()

    def _expand_selected_node(self):
        """Trigger expand action for selected node."""
        selected = self.scene.selectedItems()
        if not selected or not isinstance(selected[0], GraphNode):
            return
        
        node_item = selected[0]
        # Map scene pos to viewport global
        view_pos = self.view.mapFromScene(node_item.pos())
        global_pos = self.view.mapToGlobal(view_pos)
        self._show_context_menu(global_pos)
    
    def _show_context_menu(self, pos):
        """Show context menu for graph items."""
        item = self.view.itemAt(pos)
        
        # 1. Background Menu (No item)
        if not item:
            menu = QMenu(self)
            
            add_action = menu.addAction("➕ Add Entity")
            add_action.triggered.connect(lambda: self._add_manual_entity(pos))
            
            menu.addSeparator()
            
            layout_action = menu.addAction("🔄 Relayout Graph")
            layout_action.triggered.connect(self._restart_layout)
            
            fit_action = menu.addAction("⬜ Fit to View")
            fit_action.triggered.connect(self._fit_to_view)
            
            menu.addSeparator()
            
            clear_action = menu.addAction("🗑 Clear Graph")
            clear_action.triggered.connect(self.clear_graph)
            
            export_action = menu.addAction("📷 Save as Image")
            export_action.triggered.connect(self._export_image)
            
            menu.exec(self.view.mapToGlobal(pos))
            return
            
        # Walk up parent chain
        while item and not isinstance(item, (GraphNode, GraphEdge)):
             if item.parentItem():
                 item = item.parentItem()
             else:
                 break
        
        # 2. Node Menu
        if isinstance(item, GraphNode):
            menu = QMenu(self)
            
            # Node Info
            node_data = item.node_data
            
            # Header
            header = menu.addAction(f"{GraphNode.ENTITY_ICONS.get(node_data.entity_type, '⚡')} {node_data.value}")
            header.setEnabled(False)
            menu.addSeparator()

            # Connection
            connect_action = menu.addAction("🔗 Connect to...")
            connect_action.triggered.connect(lambda: self._start_connection_mode(item))
            menu.addSeparator()
            
            # -- Transforms based on entity type --
            transforms_menu = menu.addMenu("🚀 Run Transform")
            
            transforms = self._get_transforms_for_type(node_data.entity_type)
            if transforms:
                for t_name, t_display in transforms.items():
                    action = transforms_menu.addAction(t_display)
                    action.triggered.connect(lambda checked, n=t_name: self.transform_requested.emit(node_data, n))
            else:
                no_trans = transforms_menu.addAction("No transforms available")
                no_trans.setEnabled(False)
                
            # -- Machines --
            machines_menu = menu.addMenu("🤖 Run Machine")
            
            if hasattr(self, 'machine_manager'):
                machines = self.machine_manager.get_machines_for_type(node_data.entity_type)
                if machines:
                    for machine in machines:
                        m_action = machines_menu.addAction(machine.name)
                        m_action.triggered.connect(lambda checked, m=machine: self.machine_requested.emit(node_data, m.name))
                else:
                    no_mach = machines_menu.addAction("No machines available")
                    no_mach.setEnabled(False)

            menu.addSeparator()
            
            # Selection tools
            select_menu = menu.addMenu("🎯 Selection")
            
            neighbors_action = select_menu.addAction("Target Connected Neighbors")
            neighbors_action.triggered.connect(lambda: self._select_neighbors(node_data))
            
            invert_action = select_menu.addAction("Invert Selection")
            invert_action.triggered.connect(self._invert_selection)
            
            menu.addSeparator()
            
            # Standard actions
            del_action = menu.addAction("🗑 Delete")
            del_action.triggered.connect(self._delete_selected_node)
            
            copy_action = menu.addAction("📋 Copy Value")
            copy_action.triggered.connect(lambda: QApplication.clipboard().setText(node_data.value))
            
            pin_action = menu.addAction("📌 Unpin Node" if node_data.pinned else "📌 Pin Node")
            pin_action.triggered.connect(lambda: self._toggle_pin(node_data))
            
            menu.exec(self.view.mapToGlobal(pos))
            return

        # 3. Edge Menu
        if isinstance(item, GraphEdge):
            menu = QMenu(self)
            
            rename_action = menu.addAction("✏ Rename Relationship")
            rename_action.triggered.connect(lambda: self._rename_edge(item))
            
            del_edge_action = menu.addAction("🗑 Delete Connection")
            del_edge_action.triggered.connect(lambda: self._delete_edge(item))
            
            menu.exec(self.view.mapToGlobal(pos))

    def _export_image(self):
        """Export graph as an image."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Graph Image", "graph.png", "Images (*.png *.jpg)"
        )
        if filename:
            # Create a large image of the scene content
            self.scene.clearSelection()
            rect = self.scene.itemsBoundingRect()
            rect.adjust(-50, -50, 50, 50)  # Add padding
            
            # Render with high quality
            image = self.view.grab(self.view.mapFromScene(rect).boundingRect().toRect())
            image.save(filename)

    def _toggle_pin(self, node_data: NodeData):
        """Toggle pinned state of a node."""
        node_data.pinned = not node_data.pinned

    def _select_neighbors(self, node_item_or_data):
        """Select all immediate neighbors of a node."""
        # Handle both GraphNode item and NodeData
        if isinstance(node_item_or_data, GraphNode):
            node_data = node_item_or_data.node_data
        else:
            node_data = node_item_or_data
            
        target_ids = set()
        for edge in self._edges:
            if edge.source_id == node_data.id:
                target_ids.add(edge.target_id)
            elif edge.target_id == node_data.id:
                target_ids.add(edge.source_id)
        
        for nid in target_ids:
            if nid in self._node_items:
                self._node_items[nid].setSelected(True)
    
    def _invert_selection(self):
        """Invert the current selection."""
        for item in self._node_items.values():
            item.setSelected(not item.isSelected())

    def _get_transforms_for_type(self, entity_type: str) -> Dict[str, str]:
        """Get applicable transforms for an entity type."""
        mapping = {}
        
        if entity_type in ("domain",):
            mapping.update({
                "Email Harvester": "📧 Email Harvester",
                "Domain Infrastructure": "🏗 Domain Infra Scan",
                "Subdomain Enum": "🔗 Subdomain Enumeration",
                "Wayback Machine": "🕰 Wayback Machine",
                "Shodan Lookup": "🦅 Shodan Lookup",
                "Document Metadata": "📄 Document Metadata",
                "VirusTotal Lookup": "🦠 VirusTotal Analysis",
            })
            
        if entity_type in ("ip", "netblock"):
            mapping.update({
                "GeoIP Lookup": "🌍 GeoIP Lookup",
                "Reverse DNS": "computer Reverse DNS",
                "Shodan Lookup": "🦅 Shodan Lookup",
                "VirusTotal Lookup": "🦠 VirusTotal Analysis",
            })
            
        if entity_type in ("username", "person"):
            mapping.update({
                "Social Profile Lookup": "👤 Social Profile Lookup",
            })
            
        if entity_type in ("email",):
            mapping.update({
                "Social Profile Lookup": "👤 Social Profile Lookup",
            })
            
        if entity_type in ("phone",):
            mapping.update({
                "Phone Number Recon": "📱 Phone Number Recon",
            })
            
        if entity_type in ("url",):
            mapping.update({
                "Wayback Machine": "🕰 Wayback Machine",
            })
            
        return mapping
