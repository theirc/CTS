// Constructor
function AjaxLoader(id, options) {
    // Convert color Hex to RGB
    function HexToRGB(hex) {
        var shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
        hex = hex.replace(shorthandRegex, function (m, r, g, b) {
            return r + r + g + g + b + b;
        });
        var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    // Convert color RGB to Hex
    function RGBToHex(r, g, b) {
        return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }

    // Default options use when constructor's options are ommited
    var defaultOptions = {
        size: 32,       // Width and height of the spinner
        factor: 0.25,   // Factor of thickness, density, etc.
        speed: 1,       // Number of turns per second
        color: "#000",  // Color #rgb or #rrggbb
        clockwise: true // Direction of rotation
    }

    var size, factor, color, speed, clockwise,  // local options variables
        timer, rate = 0.0, deltaRate, segments, thickness, deltaAngle,
        fps = 30        // frames per second;
    if (options != null) {
        // Verify each field of the options
        size = "size" in options ? options.size : defaultOptions.size;
        factor = "factor" in options ? options.factor : defaultOptions.factor;
        color = HexToRGB("color" in options ? options.color : defaultOptions.color);
        speed = "speed" in options ? options.speed : defaultOptions.speed;
        clockwise = "clockwise" in options ? options.clockwise : defaultOptions.clockwise;
    } else {
        // Options are ommited, take it from default
        size = defaultOptions.size;
        factor = defaultOptions.factor;
        color = HexToRGB(defaultOptions.color);
        speed = defaultOptions.speed;
        clockwise = defaultOptions.clockwise;
    }

    var canvas = document.getElementById(id);
    if (canvas == null) {
        return null;
    }
    var context = canvas.getContext("2d");
    Init();

    // Init all viriables
    function Init() {
        segments = (size >= 32) ? ((size >= 128) ? 72 : 36) : 18,
        thickness = 0.5 * size * factor,
        deltaAngle = 2.0 * Math.PI / segments;
        deltaRate = speed / fps;
        if (clockwise) {
            deltaRate = -deltaRate;
        }
        canvas.width = size;
        canvas.height = size;
    }

    // Draw ajaxloader
    function Draw(rate) {
        var angle = 2.0 * Math.PI * rate;
        var cosA = Math.cos(angle),
            sinA = Math.sin(angle),
            x0 = 0.5 * size * (1 + cosA),
            y0 = 0.5 * size * (1 - sinA),
            x1 = x0 - thickness * cosA,
            y1 = y0 + thickness * sinA;
        context.clearRect(0, 0, size, size);
        for (var i = 0; i < segments; i++) {
            context.beginPath();
            if (clockwise) {
                context.fillStyle = "rgba(" + color.r + "," + color.g + "," + color.b + "," + (segments - 1 - i) / (segments - 1) + ")";
            } else {
                context.fillStyle = "rgba(" + color.r + "," + color.g + "," + color.b + "," + i / (segments - 1) + ")";
            }
            context.moveTo(x0, y0);
            context.lineTo(x1, y1);
            angle += deltaAngle,
            cosA = Math.cos(angle);
            sinA = Math.sin(angle);
            x0 = 0.5 * size * (1 + cosA);
            y0 = 0.5 * size * (1 - sinA);
            x1 = x0 - thickness * cosA;
            y1 = y0 + thickness * sinA;
            context.lineTo(x1, y1);
            context.lineTo(x0, y0);
            context.closePath();
            context.fill();
        }
    }

    // Show and begin animation
    this.show = function () {
        canvas.removeAttribute("style");
        clearInterval(timer);
        timer = setInterval(function () {
            Draw(rate);
            rate += deltaRate;
            rate = rate - Math.floor(rate);
        }, 1000 / fps);
    }

    // Stop animation and hide indicator
    this.hide = function () {
        clearInterval(timer);
        canvas.style.display = "none";
    }

    this.getSize = function () {
        return size;
    }

    this.setSize = function (value) {
        size = value;
        Init();
    }

    this.getFactor = function () {
        return factor;
    }

    this.setFactor = function (value) {
        factor = value;
        Init();
    }

    this.getSpeed = function () {
        return speed;
    }

    this.setSpeed = function (value) {
        speed = value;
        Init();
    }

    this.getColor = function () {
        return RGBToHex(color.r, color.g, color.b);
    }

    this.setColor = function (value) {
        color = HexToRGB(value);
    }

    this.getClockwise = function () {
        return clockwise;
    }

    this.setClockwise = function (value) {
        clockwise = value;
        Init();
    }
}
