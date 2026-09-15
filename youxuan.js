// ============================================================
// 诗词优选 · 独立页面逻辑
// ============================================================

// 全局状态
var RANKINGS = null;        // 榜单数据
var POEMS_MAP = {};         // poem_id -> poem 对象
var state = {
    genre: null,      // 体裁：'五绝' | '七绝' | '词牌|浣溪沙' ...
    category: null,   // 类别：'写景' | '抒情' | '其他' | null
    level: null,      // 榜单：'premium' | 'excellent'
    key: null         // 组合后的 key，如 '七绝|写景' 或 '词牌|浣溪沙'
};

// 词牌列表（与主脚本一致）
var TOP20_CIPAI = [
    '踏莎行', '鹧鸪天', '浣溪沙', '临江仙', '蝶恋花',
    '清平乐', '西江月', '菩萨蛮', '虞美人', '南乡子',
    '长相思', '卜算子', '采桑子', '减字木兰花', '沁园春',
    '水调歌头', '念奴娇', '满江红', '苏幕遮', '定风波'
];
var STANDARD_GENRES = ['五绝', '五律', '七绝', '七律'];
var CATEGORIES = ['写景', '抒情', '其他'];

// ============================================================
// 初始化
// ============================================================
function init() {
    // 建立 poem_id -> poem 的映射
    if (typeof POEMS_DATA !== 'undefined') {
        POEMS_DATA.forEach(function(p) {
            POEMS_MAP[p.poem_id] = p;
        });
    }

    // 加载榜单 JSON
    fetch('poem_rankings_final.json')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            RANKINGS = data;
            document.getElementById('loading').style.display = 'none';
            // 显示统计信息
            if (data._statistics) {
                var s = data._statistics;
                document.getElementById('statLine').textContent =
                    '全站共 ' + s.total_poems + ' 首 · 精品 ' + s.premium_count +
                    ' 首 · 优秀 ' + s.excellent_count + ' 首 · 合计约 ' + s.percentage;
            }
            buildGenreGrid();
            updateBreadcrumb();
            showPanel('panel-level1');
        })
        .catch(function(err) {
            document.getElementById('loading').textContent = '❌ 榜单数据加载失败：' + err.message;
        });
}

// ============================================================
// 面板切换
// ============================================================
function showPanel(id) {
    document.querySelectorAll('.panel').forEach(function(p) {
        p.classList.remove('active');
    });
    var panel = document.getElementById(id);
    if (panel) panel.classList.add('active');
}

// ============================================================
// 面包屑
// ============================================================
function updateBreadcrumb() {
    var bc = document.getElementById('breadcrumb');
    var html = '<span class="crumb" onclick="resetToLevel1()">诗词优选</span>';

    if (state.genre) {
        var displayGenre = state.genre.indexOf('词牌|') === 0 ? state.genre.split('|')[1] : state.genre;
        html += '<span class="sep">›</span><span class="crumb" onclick="backToGenre()">' + displayGenre + '</span>';
    }
    if (state.category) {
        html += '<span class="sep">›</span><span class="crumb" onclick="backToCategory()">' + state.category + '</span>';
    }
    if (state.level) {
        var levelName = state.level === 'premium' ? '精品榜单' : '优秀榜单';
        html += '<span class="sep">›</span><span class="current">' + levelName + '</span>';
    }
    bc.innerHTML = html;
}

// ============================================================
// 第一层：体裁
// ============================================================
function buildGenreGrid() {
    var grid = document.getElementById('genreGrid');
    grid.innerHTML = '';
    var allGenres = STANDARD_GENRES.concat(TOP20_CIPAI).concat(['其他词牌']);

    allGenres.forEach(function(g) {
        var key, hasData = false;
        if (STANDARD_GENRES.indexOf(g) >= 0) {
            // 标准体裁：检查是否有任意一个 "体裁|类别" 存在
            key = g;
            hasData = CATEGORIES.some(function(c) {
                return RANKINGS[g + '|' + c];
            });
        } else {
            // 词牌
            key = '词牌|' + g;
            hasData = !!RANKINGS[key];
        }
        if (!hasData) return;

        var btn = document.createElement('button');
        btn.textContent = g;
        btn.onclick = function() { selectGenre(key, g); };
        grid.appendChild(btn);
    });
}
function selectGenre(key, displayName) {
    state.genre = key;
    // 判断是否是标准体裁
    if (STANDARD_GENRES.indexOf(key) >= 0) {
        // 四种标准体裁：进入第二层，选择类别
        state.category = null;
        state.level = null;
        state.key = null;
        buildCategoryGrid();
        updateBreadcrumb();
        showPanel('panel-level2');
    } else {
        // 词牌类：直接进入第三层，选择精品/优秀
        state.category = null;
        state.key = key;
        buildLevelGrid();
        updateBreadcrumb();
        showPanel('panel-level3');
    }
}

// ============================================================
// 第二层：类别（写景/抒情/其他）
// ============================================================
function buildCategoryGrid() {
    var grid = document.getElementById('categoryGrid');
    grid.innerHTML = '';
    CATEGORIES.forEach(function(c) {
        var key = state.genre + '|' + c;
        if (!RANKINGS[key]) return; // 无数据跳过
        var btn = document.createElement('button');
        btn.textContent = c;
        btn.onclick = function() { selectCategory(c); };
        grid.appendChild(btn);
    });
}

function selectCategory(c) {
    state.category = c;
    state.key = state.genre + '|' + c;
    state.level = null;
    buildLevelGrid();
    updateBreadcrumb();
    showPanel('panel-level3');
}

// ============================================================
// 第三层：精品/优秀
// ============================================================
function buildLevelGrid() {
    var grid = document.getElementById('levelGrid');
    grid.innerHTML = '';
    var data = RANKINGS[state.key];
    if (!data) return;

    if (data.premium && data.premium.length > 0) {
        var btnP = document.createElement('button');
        btnP.className = 'premium-btn';
        btnP.textContent = '✨ 精品榜单（' + data.premium.length + '）';
        btnP.onclick = function() { selectLevel('premium'); };
        grid.appendChild(btnP);
    }
    if (data.excellent && data.excellent.length > 0) {
        var btnE = document.createElement('button');
        btnE.className = 'excellent-btn';
        btnE.textContent = '🌟 优秀榜单（' + data.excellent.length + '）';
        btnE.onclick = function() { selectLevel('excellent'); };
        grid.appendChild(btnE);
    }
}

function selectLevel(level) {
    state.level = level;
    buildModeGrid();
    updateBreadcrumb();
    showPanel('panel-level4');
}

// ============================================================
// 第四层：展示模式（欣赏/复制保存）
// ============================================================
function buildModeGrid() {
    var grid = document.getElementById('modeGrid');
    grid.innerHTML = '';

    var btn1 = document.createElement('button');
    btn1.textContent = '👁 欣赏';
    btn1.onclick = function() { gotoEnjoy(); };
    grid.appendChild(btn1);

    var btn2 = document.createElement('button');
    btn2.textContent = '📋 复制保存';
    btn2.onclick = function() { gotoCopyMode(); };
    grid.appendChild(btn2);
}

// 跳回主脚本欣赏
function gotoEnjoy() {
    var url = 'index.html?youxuan=1&key=' + encodeURIComponent(state.key) + '&level=' + state.level;
    window.location.href = url;
}

// 在本页面显示纯文本合辑
function gotoCopyMode() {
    var data = RANKINGS[state.key];
    if (!data) return;
    var ids = data[state.level] || [];

    // 构建显示和纯文本
    var html = '';
    var text = '';
    var displayGenre = state.genre.indexOf('词牌|') === 0 ? state.genre.split('|')[1] : state.genre;
    var levelName = state.level === 'premium' ? '精品榜单' : '优秀榜单';
    var titleLine = displayGenre + (state.category ? ' · ' + state.category : '') + ' · ' + levelName;

    var stat = document.getElementById('statLine');
    var tipHtml = '';
    if (state.level === 'premium') {
        tipHtml = '✨ 精品榜单 · 由 DeepSeek 与 MiniMax 两大模型交叉比对得出，双模型共识优先。代表了本类诗词中最受两大 AI 共同推崇的作品。';
    } else {
        tipHtml = '🌟 优秀榜单 · 由 DeepSeek 与 MiniMax 两大模型分别筛选，两方所选合并而成（已排除精品榜单中的作品）。代表了本类诗词中值得认真一读的佳作。';
    }

    html += '<div class="stat">' + tipHtml + '</div>';
    html += '<div class="stat">共 ' + ids.length + ' 首 · ' + titleLine + '</div>';

    ids.forEach(function(pid) {
        var poem = POEMS_MAP[pid];
        if (!poem) return;
        html += '<div class="poem-item">';
        html += '<div class="t">' + poem.title + '</div>';
        html += '<div class="a">冰雪</div>';
        if (poem.date) html += '<div class="d">' + poem.date + '</div>';
        html += '<div class="b">' + poem.body.replace(/\n/g, '<br>') + '</div>';
        html += '</div>';

        // 纯文本
        text += poem.title + '\n\n冰雪\n' + (poem.date || '') + '\n\n' + poem.body;
        text += '\n\n';
    });

    document.getElementById('copyContent').innerHTML = html;
    window._copyText = text.trim();

    showPanel('panel-copy');
}

function copyAll() {
    var text = window._copyText || '';
    if (!text) return;
    var btn = document.getElementById('copyBtn');
    var doCopy = function(t) {
        if (navigator.clipboard) {
            return navigator.clipboard.writeText(t);
        } else {
            return new Promise(function(resolve) {
                var dummy = document.createElement('textarea');
                document.body.appendChild(dummy);
                dummy.value = t;
                dummy.select();
                document.execCommand('copy');
                document.body.removeChild(dummy);
                resolve();
            });
        }
    };
    doCopy(text).then(function() {
        if (btn) {
            btn.textContent = '✅ 已复制';
            setTimeout(function() { btn.textContent = '📋 一键复制全部'; }, 1500);
        }
    }).catch(function() {
        alert('复制失败，请手动选择文本复制');
    });
}

function backToLevel4() {
    showPanel('panel-level4');
}

// ============================================================
// 返回导航
// ============================================================
function resetToLevel1() {
    state = { genre: null, category: null, level: null, key: null };
    updateBreadcrumb();
    showPanel('panel-level1');
}

function backToGenre() {
    state.category = null;
    state.level = null;
    state.key = null;
    updateBreadcrumb();
    if (STANDARD_GENRES.indexOf(state.genre) >= 0) {
        buildCategoryGrid();
        showPanel('panel-level2');
    } else {
        showPanel('panel-level1');
    }
}

function backToCategory() {
    state.level = null;
    state.key = state.genre + '|' + state.category;
    buildLevelGrid();
    updateBreadcrumb();
    showPanel('panel-level3');
}

// ============================================================
// 启动
// ============================================================
window.addEventListener('DOMContentLoaded', init);