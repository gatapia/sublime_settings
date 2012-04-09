
goog.require('namespace.parent');

goog.provide('namespace.child');


/**
 * @constructor
 * @extends {namespace.parent}
 */
namespace.child = {
  namespace.parent.call(this);
  /** @type {string} */
  this.prop1 = '';
  /** @type {number} */
  this.prop2 = 1;
};
goog.inherits(namespace.child, namespace.parent);

/** Function 1 */
namespace.child.prototype.func1 = function() {};

/** Function 2 */
namespace.child.prototype.func2 = function() {};