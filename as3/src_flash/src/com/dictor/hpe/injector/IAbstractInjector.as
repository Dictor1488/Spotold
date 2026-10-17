package com.dictor.hpe.injector
{
   import flash.events.IEventDispatcher;

   public interface IAbstractInjector extends IEventDispatcher
   {
      function get componentName():String;
      function get componentUI():Class;
   }
}
