package com.dictor.spot.battle {
    import com.dictor.hpe.injector.BattleDisplayable;
    import flash.display.DisplayObject;
    import flash.display.DisplayObjectContainer;
    import flash.display.Sprite;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.utils.Dictionary;

    public class SpotPanel extends BattleDisplayable {
        private var states:Dictionary = new Dictionary();
        private var rows:Dictionary = new Dictionary();
        private var icons:Array = ["missing", "detected", "undetected", ""];
        private var style:int = 1;
        private var offset:int = 0;
        private var align:int = 1;
        private var colorblind:Boolean = false;
        private var active:Boolean = true;

        public function SpotPanel() {
            super();
            name = "inqSpotPanel";
        }
        private function member(o:*, key:String):* {
            try { return o ? o[key] : null; } catch (e:Error) { return null; }
        }
        private function getHolder(list:*, id:int):* {
            if (!list) return null;
            try { return list.getHolderByVehicleID(id); } catch (e:Error) {}
            try { return list.getHolderByVehicleId(id); } catch (e2:Error) {}
            return null;
        }
        private function getItem(id:int):* {
            var page:* = battlePage;
            var panel:* = member(page, "playersPanel");
            if (!panel) panel = member(page, "epicRandomPlayersPanel");
            if (!panel) return null;
            var holder:* = getHolder(member(panel, "listRight"), id);
            if (!holder) return null;
            try { return holder.getListItem(); } catch (e:Error) {}
            var item:* = member(holder, "_listItem");
            return item ? item : member(holder, "listItem");
        }
        private function ensure(id:int, item:*):TextField {
            var text:TextField = rows[id] as TextField;
            if (!text) {
                text = new TextField();
                text.name = "inqSpot_" + id;
                text.width = 24;
                text.height = 24;
                text.mouseEnabled = false;
                text.selectable = false;
                text.multiline = false;
                rows[id] = text;
            }
            if (item is DisplayObjectContainer && text.parent != item) {
                if (text.parent) text.parent.removeChild(text);
                DisplayObjectContainer(item).addChild(text);
            }
            return text;
        }
        private function redraw(id:int):void {
            var state:* = states[id];
            var item:* = getItem(id);
            var text:TextField = rows[id] as TextField;
            if (!item || state == null || !active) {
                if (text) text.visible = false;
                return;
            }
            text = ensure(id, item);
            var index:int = int(state);
            var icon:String = index >= 1 && index <= 4 ? String(icons[index-1]) : "";
            if (index == 3 && colorblind) icon = "colorblind";
            if (index == 4 || icon == "") {
                text.visible = false;
                return;
            }
            var anchor:DisplayObject = member(item, "vehicleIcon") as DisplayObject;
            if (!anchor) anchor = member(item, "vehicleTF") as DisplayObject;
            text.x = Math.round(anchor ? anchor.x + (align == 0 ? -109 : 22) + offset : offset);
            text.y = Math.round(anchor ? anchor.y : 0);
            text.htmlText = '<img src="img://gui/spottedstatus/styles/' + style + '/' + icon + '.png" width="' + (style == 2 ? 15 : 19) + '" height="' + (style == 2 ? 24 : 19) + '">';
            text.visible = Boolean(member(item, "visible"));
        }
        public function as_setState(id:int, state:int):void {
            if (id <= 0) return;
            states[id] = state;
            redraw(id);
        }
        public function as_setSettings(styleValue:int, alignValue:int, xOffset:int, cb:Boolean):void {
            style = Math.max(0, Math.min(2, styleValue));
            align = alignValue == 0 ? 0 : 1;
            offset = Math.max(-150, Math.min(150, xOffset));
            colorblind = cb;
            as_refreshAll();
        }
        public function as_setVisibility(value:Boolean):void {
            active = value;
            as_refreshAll();
        }
        public function as_refreshAll():void {
            for (var key:* in states) redraw(int(key));
        }
        public function as_clear():void {
            for each (var text:TextField in rows) {
                if (text && text.parent) text.parent.removeChild(text);
            }
            rows = new Dictionary();
            states = new Dictionary();
        }
        override protected function onDispose():void {
            as_clear();
            super.onDispose();
        }
    }
}
