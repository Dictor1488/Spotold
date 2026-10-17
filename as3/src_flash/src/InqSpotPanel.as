package {
    import com.dictor.hpe.injector.AbstractViewInjector;
    import com.dictor.hpe.injector.IAbstractInjector;
    import com.dictor.spot.battle.SpotPanel;
    public class InqSpotPanel extends AbstractViewInjector implements IAbstractInjector {
        override public function get componentUI():Class { return SpotPanel; }
        override public function get componentName():String { return "inqSpotPanel"; }
    }
}
