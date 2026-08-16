/**
 * 音量调节线性化补偿脚本（方案A：prototype 劫持 + 补偿曲线）
 *
 * 原理：网易云 webplayer 滑块位置 -> audio.volume 的映射为压缩曲线，
 * 低段音量过小。本脚本在页面任何脚本运行之前（QWebEngineScript
 * DocumentCreation + MainWorld 注入）劫持 HTMLMediaElement.prototype.volume：
 *   - setter：写入时施加补偿曲线 h(v) = m · v^k（k < 1 抬高低段）
 *   - getter：读取时做逆变换 (real/m)^(1/k)，网页 UI 全程无感知
 * 播放器持久化音量到 localStorage 时读回的是"设定值"，下次恢复时再经
 * setter 补偿，闭环一致。
 *
 * m 为振幅缩放系数（0 < m ≤ 1）：压低整条曲线的下限与上限，让滑块
 * 低段获得更细的调节粒度。实测锚定：滑块 30 档响度 ≈ 旧曲线 1 档响度，
 * m=0.3 时低段粒度与最大音量上限平衡良好。
 *
 * k、m 分别挂在 window.__NC_VOLUME_K / window.__NC_VOLUME_M 上，
 * Qt 侧注入时在脚本头部写入初始值，运行时可通过 runJavaScript 修改
 * 实现热更新，无需重载页面。
 */
(function () {
    'use strict';

    // 默认参数，Qt 侧注入时会在本脚本之前写入实际配置值
    if (typeof window.__NC_VOLUME_K !== 'number') {
        window.__NC_VOLUME_K = 0.5;
    }
    if (typeof window.__NC_VOLUME_M !== 'number') {
        window.__NC_VOLUME_M = 0.3;
    }

    // 参数允许范围，与 profile_manager 中的校验保持一致
    var K_MIN = 0.2;
    var K_MAX = 1.0;
    var K_DEFAULT = 0.5;
    var M_MIN = 0.01;
    var M_MAX = 1.0;
    var M_DEFAULT = 0.3;

    function getK() {
        var k = window.__NC_VOLUME_K;
        if (typeof k !== 'number' || !isFinite(k) || k <= 0) {
            return K_DEFAULT;
        }
        return Math.min(K_MAX, Math.max(K_MIN, k));
    }

    function getM() {
        var m = window.__NC_VOLUME_M;
        if (typeof m !== 'number' || !isFinite(m) || m <= 0) {
            return M_DEFAULT;
        }
        return Math.min(M_MAX, Math.max(M_MIN, m));
    }

    function clamp01(v) {
        return Math.min(1, Math.max(0, v));
    }

    var desc = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'volume');
    if (!desc || typeof desc.get !== 'function' || typeof desc.set !== 'function') {
        // 环境异常（理论上不会发生），标记未安装，Qt 侧可检测
        window.__NC_VOLUME_COMPENSATION_INSTALLED = false;
        return;
    }

    var nativeGet = desc.get;
    var nativeSet = desc.set;

    Object.defineProperty(HTMLMediaElement.prototype, 'volume', {
        configurable: true,
        enumerable: desc.enumerable,
        get: function () {
            var real = nativeGet.call(this);
            var k = getK();
            var m = getM();
            // 逆变换：网页读回"设定值"，保持 UI 无感知
            return clamp01(Math.pow(real / m, 1 / k));
        },
        set: function (v) {
            var num = Number(v);
            if (!isFinite(num)) {
                // 非法值维持原生行为（原生 setter 自行抛错或处理）
                nativeSet.call(this, v);
                return;
            }
            var k = getK();
            var m = getM();
            nativeSet.call(this, clamp01(m * Math.pow(clamp01(num), k)));
        }
    });

    // 安装标记，供 Qt 侧 runJavaScript 验证劫持是否生效
    window.__NC_VOLUME_COMPENSATION_INSTALLED = true;
})();
